#!/usr/bin/env python3
"""Bind the adopted I32 source to native outputs and enumerate the real change.

Read-only with respect to CAD. Historical authoring recipes are not rerun.
"""
from pathlib import Path
import argparse, csv, hashlib, json, subprocess, sys, uuid
D = Path(__file__).resolve().parent
W = D.parents[1]
ROOT = W.parents[2]
sys.path.insert(0, str(W/'analyses/convergence_01/support'))
import check_combined_copper as c
BASE = '4c3e54395e84483298e453468a65ff2646e9de4e'
PCB_SHA = '45a2a679d9893d51fa641e539af45bc6ec1324169ea5f2226ecdea0ae2464da7'
FILLED_SHA = '249d7b584af71605ee160c1ff425fda16a11b3ba93458bb243a722214c66ab30'
def sha(data): return hashlib.sha256(data).hexdigest()
def put(path, value): path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(value, indent=2)+'\n')
def base(path): return subprocess.check_output(['git','show',BASE+':'+path.relative_to(ROOT).as_posix()],cwd=ROOT)
def footprints(tree): return {c.prop(f)['Reference']:f for f in c.child(tree,'footprint')}
def nets(fp): return {str(p[1]):c.get(p,'net')[1] if c.get(p,'net') else '' for p in c.child(fp,'pad') if str(p[1])}
def describe(f):
    return dict(properties=c.prop(f),footprint=str(f[1]),position=c.get(f,'at'),side=c.get(f,'layer')[0],pads=nets(f))
def items(tree):
    names={n[1]:n[2] for n in c.child(tree,'net')}
    out={}
    for kind in ['segment','via','zone']:
        for q in c.child(tree,kind):
            uid=c.get(q,'uuid')[0]; record=json.loads(json.dumps(q,default=str))
            for value in record:
                if isinstance(value,list) and value[0]=='net':value[1]=names.get(value[1],value[1])
            out[uid]=dict(kind=kind,net=names.get((c.get(q,'net')or[0])[0],''),record=record)
    return out
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--native-dir',type=Path,required=True);ap.add_argument('--out',type=Path,default=D);ap.add_argument('--procurement-redline',action='store_true');ap.add_argument('--expected-source-sha');ap.add_argument('--expected-filled-sha');a=ap.parse_args()
    global BASE, PCB_SHA, FILLED_SHA
    if a.procurement_redline:
        assert a.expected_source_sha and a.expected_filled_sha
        BASE='1c934f9ddd7a1b823e5136484f525485472528f6'
        PCB_SHA=a.expected_source_sha;FILLED_SHA=a.expected_filled_sha
    else:assert not a.expected_source_sha and not a.expected_filled_sha
    cad=W/'candidate/cad';pcb=cad/'GR86_CCA_RevB.kicad_pcb'
    assert sha(pcb.read_bytes())==PCB_SHA
    native=json.loads((a.native_dir/'RESULT.json').read_text());inv=json.loads((a.native_dir/'COPIED_SOURCE_INVENTORY.json').read_text())
    assert native['status']=='NATIVE_OUTPUTS_COMPLETE' and native['native_report_finding_count']==0 and native['inputs_unchanged']
    assert all(v['pass'] for v in native['output_postconditions'].values()) and len(native['output_postconditions'])==13
    assert native['refilled_pcb_sha256']==FILLED_SHA
    for name,digest in inv['cad_before_native'].items():assert sha((cad/name).read_bytes())==digest,name
    assert len(inv['cad_before_native'])==(157 if a.procurement_redline else 135)
    b=c.sx.loads(pcb.read_text());old=c.sx.loads(base(pcb).decode());fp=footprints(b);bf=footprints(old)
    fitted={r for r,f in fp.items() if c.prop(f).get('Assembly') in ['FACTORY','MANUAL_GPS']}
    assert len(fitted)==177
    assert {r for r,f in fp.items() if c.prop(f).get('Assembly')=='DNP'}=={'C203','R301','R306'}
    bom={r['Reference']:r for r in csv.DictReader((a.native_dir/'REVIEW_BOM.csv').open())}
    assert set(bom)==fitted and all(bom[r]['MPN']==c.prop(fp[r])['MPN'] for r in fitted)
    changes={r:dict(before=describe(bf[r]) if r in bf else None,after=describe(fp[r]) if r in fp else None) for r in sorted(set(fp)|set(bf)) if r not in fp or r not in bf or describe(fp[r])!=describe(bf[r])}
    if a.procurement_redline:
        from procurement_redline.apply_redline import SPEC
        assert set(changes)==set(SPEC)|{'R151'}, 'Frozen references plus the proven R151 source-code omission only'
        old_r151=describe(bf['R151']);new_r151=describe(fp['R151'])
        assert old_r151['properties'].get('LCSC','')=='' and new_r151['properties']['LCSC']=='C190124'
        old_r151['properties']['LCSC']='C190124'
        assert old_r151==new_r151, 'R151 MPN, package, value and placement must be unchanged'
        assert set(fp)==set(bf)
        assert all(nets(fp[r])==nets(bf[r]) for r in fp), 'Every original pad/net must survive'
        for ref,part in SPEC.items():
            assert c.prop(fp[ref])['MPN']==part['MPN'] and c.prop(fp[ref])['LCSC']==part['LCSC']
            assert str(fp[ref][1])=='RevB:I32_PROCUREMENT_'+ref
    assert c.prop(fp['U301'])['MPN']=='TCAN3403DRBRQ1'
    gpio={'5':'CAN_TX_MCU','4':'CAN_RX_MCU','18':'GPS_UART_RX','17':'GPS_UART_TX','16':'GPS_PPS','1':'OIL_ADC'}
    # Preserve complete module pin/net assignment (also EN/GPIO0/UART0), not a remembered alias.
    assert nets(fp['U201'])==nets(bf['U201'])
    for ref in ['U301','R301','R303','R306','U401','U402','U404','U502','J201']:
        if ref in fp:assert describe(fp[ref])==describe(bf[ref]),ref
    assert nets(fp['U151'])['11']=='3V3_BUCK_ENABLE'
    for ref,pin,net in [('R160','1','3V3_VIN'),('R166','1','3V3_ENABLE'),('R166','2','3V3_BUCK_ENABLE'),('U152','8','3V3_ISO_SNS'),('U153','8','+3V3'),('U153','9','3V3_BULK_SWITCHED'),('R158','1','3V3_BULK_SWITCHED'),('R158','2','3V3_BULK_DAMPED'),('C206','1','3V3_BULK_DAMPED'),('U202','4','SUP_RESET_DELAY'),('R204','1','+3V3'),('R204','2','SUP_RESET_DELAY')]:assert nets(fp[ref])[pin]==net,(ref,pin)
    assert c.get(c.child(b,'setup')[0],'stackup')==c.get(c.child(old,'setup')[0],'stackup')
    for name in ['GR86_CCA_RevB.kicad_pro','GR86_CCA_RevB.kicad_dru']:
        if (cad/name).exists():assert (cad/name).read_bytes()==base(cad/name),name
    fw={}
    for p in sorted((W/'candidate/firmware').rglob('*')):
        if p.is_file():assert p.read_bytes()==base(p),p;fw[p.relative_to(W/'candidate/firmware').as_posix()]=sha(p.read_bytes())
    olditems,newitems=items(old),items(b)
    delta={k:[dict(uuid=i,**source[i]) for i in sorted(ids)] for k,ids,source in [('added',set(newitems)-set(olditems),newitems),('removed',set(olditems)-set(newitems),olditems),('modified',set(newitems)&set(olditems),newitems)]}
    delta['modified']=[dict(r,before=olditems[r['uuid']]) for r in delta['modified'] if newitems[r['uuid']]!=olditems[r['uuid']]]
    signal_nets={str(n) for n in nets(bf['U201']).values() if any(s in str(n) for s in ['CAN','GPS','PPS','UART','OIL_ADC','RF'])}
    signal_changes=[r for rows in delta.values() for r in rows if r['net'] in signal_nets]
    assert not signal_changes,signal_changes
    vias={c.get(v,'uuid')[0]:v for v in c.child(b,'via')}
    sourcevias=json.loads((W/'candidate/verification/I13/SOURCE_CHANGE_CHECK.json').read_text())['new_vias']
    vip=[]
    for row in sourcevias:
        v=vias[row['uuid']];assert c.get(v,'at')==row['xy'];vip.append(dict(reference='U201.41',uuid=row['uuid'],xy=c.get(v,'at'),drill=c.get(v,'drill')[0],land=c.get(v,'size')[0]))
    r=fp['R153'];p=next(p for p in c.child(r,'pad') if str(p[1])=='2');x,y=c.get(r,'at')[:2];px,py=c.get(p,'at')[:2];sx,sy=c.get(p,'size')
    vv=[(u,v)for u,v in vias.items()if abs(c.get(v,'at')[0]-x-px)<=sx/2 and abs(c.get(v,'at')[1]-y-py)<=sy/2];assert len(vv)==1
    u,v=vv[0];vip.append(dict(reference='R153.2',uuid=u,xy=c.get(v,'at'),drill=c.get(v,'drill')[0],land=c.get(v,'size')[0]));assert len(vip)==49
    oldvia={c.get(v,'uuid')[0]:v for v in c.child(old,'via')}
    assert all(vias[q['uuid']]==oldvia[q['uuid']] for q in vip)
    newvia=[v for u,v in vias.items() if u not in oldvia]
    assert all(c.get(v,'size')[0]>=.6 and c.get(v,'drill')[0]>=.3 for v in newvia)
    from shapely.geometry import Polygon
    keepout_review=[]
    kz=lambda t:{c.get(z,'uuid')[0]:z for z in c.child(t,'zone') if c.child(z,'keepout')}
    ko,kn=kz(old),kz(b);assert ko.keys()==kn.keys()
    for ident,q in kn.items():
        z=ko[ident]
        assert sorted(c.get(q,'layers')or c.get(q,'layer'))==sorted(c.get(z,'layers')or c.get(z,'layer'))
        assert c.get(q,'keepout')==c.get(z,'keepout')
        poly=lambda v:Polygon([p[1:]for p in c.child(c.child(c.child(v,'polygon')[0],'pts')[0],'xy')])
        p0,p1=poly(z),poly(q)
        hd=p0.hausdorff_distance(p1);area=p0.symmetric_difference(p1).area
        assert hd<1e-6 and area<1e-4,(ident,hd,area)
        keepout_review.append(dict(uuid=ident,hausdorff_mm=hd,symmetric_difference_mm2=area,rule_and_layer_sets_identical=True))
    out=dict(status='PASS_CURRENT_SOURCE_BINDING_AND_PRESERVED_CONTRACTS',base_commit=BASE,source_PCB_sha256=PCB_SHA,filled_PCB_sha256=FILLED_SHA,native_CAD_inputs_verified=len(inv['cad_before_native']),native_schematic_XML_sha256=sha((a.native_dir/'SCHEMATIC_NETLIST.xml').read_bytes()),fitted_parts=177,new_references=sorted(set(fp)-set(bf)),removed_references=sorted(set(bf)-set(fp)),part_changes=changes,copper_delta=delta,firmware_unchanged_from_base=True,firmware_files=fw,U201_pin_nets=nets(fp['U201']),receive_only_CAN=dict(transceiver='TCAN3403DRBRQ1',R301='DNP_OPEN',R306='DNP',bus='Classical 500kbit/s',source_and_firmware_unchanged=True),RF_CAN_GPS_oil_signal_copper_unchanged=True,keepout_rules_preserved=True,keepout_native_nanometre_quantization=keepout_review,stackup_and_native_rules_unchanged=True,new_ordinary_vias=len(newvia),filled_capped_planarized_vias=vip,physical_tests=0)
    put(a.out/'SOURCE_AUDIT.json',out)
    put(a.out/'SOURCE_BINDING.json',dict(status='CURRENT_I32_PROCUREMENT_REDLINE' if a.procurement_redline else 'CURRENT_I32',source_PCB_sha256=PCB_SHA,filled_PCB_sha256=FILLED_SHA,native_schematic_XML_sha256=out['native_schematic_XML_sha256'],cad_files=inv['cad_before_native'],firmware_files=fw))
    put(a.out/'AUTHORED_CHANGES.json',dict(status='ADOPTED_AND_NATIVE_VERIFIED',base_commit=BASE,source_PCB_sha256=PCB_SHA,parts=changes,copper_counts={k:len(v)for k,v in delta.items()},detail='SOURCE_AUDIT.json'))
    # Only extant task UUIDs are accepted. Earlier routing attempts remain history.
    tasks=json.loads((D/'history/STAGE170_ROUTE_TASKS.json').read_text())+json.loads((D/'CONTROLLED_ROUTE_TASKS.json').read_text())
    uid=lambda s:str(uuid.uuid5(uuid.NAMESPACE_URL,'GR86-I32-route:'+s))
    adopted={}
    for task in tasks:
        present=[u for u in [uid(task['id'])]+[uid(task['id']+':'+str(j))for j in range(200)] if u in newitems]
        if present:adopted[task['id']]=dict(task=task,actual_copper_uuids=present,complete_native_connectivity=True)
    put(a.out/'ADOPTED_ROUTE_INVENTORY.json',dict(source_PCB_sha256=PCB_SHA,routes=list(adopted.values()),note='Task endpoints are authoring intent; exact surviving coordinates/nets are in SOURCE_AUDIT and LAYOUT_MEASUREMENTS. Rejected/partially replaced attempts remain in history.'))
    print(json.dumps(dict(status=out['status'],new_refs=out['new_references'],copper_counts={k:len(v)for k,v in delta.items()},firmware_files=len(fw),VIP=len(vip)),indent=2))
if __name__=='__main__':main()
