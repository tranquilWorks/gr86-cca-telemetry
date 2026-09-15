#!/usr/bin/env python3
"""Read captured public JLC responses; retain exact identity and ordering fields.

No cart, order, substitution, login, or supplier communication is performed.
The HTTP acquisition timestamps and digests are preserved separately from
this deterministic extraction. Ephemeral signed download URLs are excluded.
"""
from pathlib import Path
import argparse,hashlib,json,re,shutil,datetime
from apply_redline import SPEC

def records(text):
    result={}
    for raw in re.findall(r'self\.__next_f\.push\(\[1,("(?:[^"\\]|\\.)*")\]\)',text):
        for line in json.loads(raw).splitlines():
            m=re.match(r'([0-9a-f]+):(.*)',line)
            if m:
                try:result[m[1]]=json.loads(m[2])
                except ValueError:pass
    return result

def walk(v):
    if isinstance(v,dict):
        yield v
        for x in v.values():yield from walk(x)
    elif isinstance(v,list):
        for x in v:yield from walk(x)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--captures',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    rows=[]
    for cn in sorted({s['LCSC']for s in SPEC.values()}):
        p=a.captures/('L121-jlc.html'if cn=='C6471075'else cn+'.html')
        rec=records(p.read_text());flat=[v for root in rec.values()for v in walk(root)]
        base=next(v for v in flat if v.get('componentCode')==cn and 'assemblyMode'in v)
        buy=next(v for v in flat if v.get('componentCode')==cn and 'isBuyComponent'in v)
        refs=sorted(r for r,s in SPEC.items()if s['LCSC']==cn);expected=SPEC[refs[0]]['MPN']
        assert base['componentModelEn']==buy['componentModelEn']==expected
        assert buy['isBuyComponent']=='1'and buy['allowPostFlag'] is True and not buy.get('noBuyReason')
        stamp=json.loads((a.captures/(cn+'.json')).read_text())['retrieved_at']if(cn!='C6471075')else datetime.datetime.fromtimestamp(p.stat().st_mtime,datetime.timezone.utc).isoformat()
        rows.append(dict(refs=refs,MPN=expected,LCSC=cn,url='https://jlcpcb.com/partdetail/'+cn,retrieved_at_UTC=stamp,response_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),package=base['componentSpecificationEn'],assemblyMode=base['assemblyMode'],description=base['describe'],datasheet_url=base['dataManualUrl'],stock=buy['overseasStockCount'],preorder_minimum=buy['preMinPurchaseNum'],canPresaleNumber=buy.get('canPresaleNumber'),isBuyComponent=buy['isBuyComponent'],allowPostFlag=buy['allowPostFlag'],noBuyReason=buy.get('noBuyReason'),status='CATALOG_PURCHASABLE_STOCK'if buy['overseasStockCount']>0 else'CATALOG_PREORDER_PATH_AVAILABLE'))
    out=dict(status='PASS_EXACT_MPN_CNUMBER_AND_PUBLIC_PURCHASE_PATHS',unique_parts=len(rows),changed_fitted_references=sum(len(r['refs'])for r in rows),rows=rows,stock_reserved=False,order_placed=False,authenticated_orderability_test=False,physical_assembly_validated=False,L121_factory_process_note='JLC lists this SMD part as manualWeld (public UI: Wave Soldering). It remains a factory-supplied placement in the 175-row CPL. This is not proof of automatic SMT handling; exact supplier process and orientation approval remain required before ordering. F101/U401 remain the only local-install exceptions.',scope='Public exact-identity catalog/sourceability and preorder availability snapshot; inventory and supplier process acceptance are not guaranteed.')
    (a.out/'LIVE_JLC_SOURCEABILITY.json').write_text(json.dumps(out,indent=2)+'\n');print([(r['LCSC'],r['stock'],r['assemblyMode'],r['status'])for r in rows])
if __name__=='__main__':main()
