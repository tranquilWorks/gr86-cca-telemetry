#!/usr/bin/env python3
"""Source-bound package, pad/net, stencil and generic-model checks."""
from pathlib import Path
import hashlib,json,sys,math,shutil
D=Path(__file__).resolve().parent;W=D.parents[2];CAD=W/'candidate/cad'
sys.path.insert(0,str(W/'analyses/convergence_01/support'))
import check_combined_copper as c
from apply_redline import SPEC,MODEL_BOUNDS

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 b,items,unsupported=c.collect(CAD/'GR86_CCA_RevB.kicad_pcb');assert not unsupported
 fps={c.prop(f)['Reference']:f for f in c.child(b,'footprint')};old=json.loads((D/'AUTHORED_REDLINE.json').read_text())['before'];rows=[]
 dims={'L121':([5.4,2.8],[[0,-4.9],[0,4.9]]),'R156':([.9144,1.7018],[[-1.524,0],[1.524,0]]),'R160':([1,1.45],[[-1.025,0],[1.025,0]])}
 for ref,spec in SPEC.items():
  f=fps[ref];pads=c.child(f,'pad');prev=old[ref]['pads'];assert str(f[1])=='RevB:I32_PROCUREMENT_'+ref
  assert len(pads)==len(prev)==(8 if ref=='U101'else 2)
  assert {(str(p[1]),tuple(c.get(p,'net')))for p in pads}=={(str(p[1]),tuple(c.get(p,'net')))for p in prev}
  side=c.get(f,'layer')[0];assert all(set(c.get(p,'layers'))=={side,side.replace('Cu','Paste'),side.replace('Cu','Mask')}for p in pads)
  assert all(not c.get(p,'solder_paste_margin')and not c.get(p,'solder_paste_margin_ratio')for p in pads)
  if spec['MPN'].startswith('PTFR'):expected=([.9,1.2],[[-.95,0],[.95,0]])
  else:expected=dims.get(ref)
  if expected:
   size,locations=expected
   for p,xy in zip(sorted(pads,key=lambda p:p[1]),locations):
    assert all(abs(a-z)<1e-7 for a,z in zip(c.get(p,'size'),size))
    assert all(abs(a-z)<1e-7 for a,z in zip(c.get(p,'at')[:2],xy))
  else:
   assert all(c.get(p,'size')==c.get(q,'size')and c.get(p,'at')==c.get(q,'at')for p,q in zip(pads,prev)),ref
  clearances=[]
  for p in pads:
   geom=c.pad_shape(f,p);net=c.get(p,'net')[0]
   clearances.extend(geom.distance(it['geometry'])for it in items if it['layer']==side and it['net']!=net and it['geometry'].distance(geom)<2)
  assert min(clearances)>.149997,ref
  model=c.child(f,'model');assert len(model)==1
  row=dict(ref=ref,MPN=spec['MPN'],LCSC=spec['LCSC'],library=str(f[1]),footprint_sha256=sha(CAD/'libraries/RevB.pretty'/('I32_PROCUREMENT_'+ref+'.kicad_mod')),side=side,at=c.get(f,'at'),pads=[dict(number=p[1],at=c.get(p,'at'),size=c.get(p,'size'),net=c.get(p,'net')[1],layers=c.get(p,'layers'))for p in pads],pad_nets_unchanged=True,copper_clearance_min_mm=min(clearances),mask_paste='Native per-pad copper/mask/paste layers; no local paste reduction override; global project settings retained',model_reference=model[0][1])
  if ref in MODEL_BOUNDS:
   mp=CAD/'models'/('ENVELOPE_I32_PROCUREMENT_'+ref+'.step');row.update(maximum_body_mm=MODEL_BOUNDS[ref],model_sha256=sha(mp),model_kind='Generic manufacturer-dimensional maximum-body envelope; not vendor CAD')
  else:row.update(model_kind='Retained KiCad nominal generic package; maximum body/tolerance separately covered by mechanical courtyard +0.30 mm and height allocation')
  rows.append(row)
 sources=[('L121-manufacturer.pdf','Chilisin/Pulse BPCI series, p2: BPCI00121280 body and recommended PCB lands','https://jlcpcb.com/partdetail/C6471075'),('R156-plt.pdf','Vishay PLT Rev 11-May-2026: 1206 body and electrical limits','https://www.vishay.com/docs/60030/plt.pdf'),('R156-landpatterns.pdf','Vishay 60119, p1: 1206 recommended land pattern','https://www.vishay.com/docs/60119/landpatterns.pdf'),('C864499.pdf','YAGEO RT V16, 6-May-2025, p4: RT0805 dimensions','https://jlcpcb.com/partdetail/C864499'),('C19679768.pdf','Resistor.Today PTFR, p3: 0603 maximum dimensions and land pattern','https://jlcpcb.com/partdetail/C19679768'),('C342967.pdf','TDK CGA series: ordering-code dimensions, CGA3 E maximum body; exact T0Y0N catalog identity bound by current JLC record','https://jlcpcb.com/partdetail/C342967'),('C688370.pdf','Analog Devices LTC4367: H-grade ordering table and MS8 drawing 05-08-1660 Rev G','https://jlcpcb.com/partdetail/C688370')]
 refs=D/'references';refs.mkdir(exist_ok=True);index=[]
 for name,basis,url in sources:
  target=refs/name
  assert target.is_file(), 'Missing retained manufacturer evidence: '+name
  index.append(dict(file=name,sha256=sha(target),basis=basis,source_url=url))
 notes={
 'L121':'Manufacturer lands: 5.4 mm width, 2.8 mm depth, 7.0 mm inside gap, 12.6 mm overall; pad centres +/-4.9 mm. 12.5 x12.5 x8.0 mm maximum body, 13.1 mm courtyard. Local 90 degree rotation puts pads along PCB X; passive winding has no electrical polarity. All switch/return networks retained; exact assembly feed orientation remains a supplier setup check.',
 'R156':'Vishay 60119: 0.156 in overall, 0.084 in inner gap, 0.036 in pad length, 0.067 in width. Converted without scaling the old 0603. 3.4032 x1.7272 x0.8382 mm maximum body. Nonpolar. Original ground-pad centre retained.',
 'R160':'1.0 x1.45 mm standard 0805 lands at +/-1.025 mm; RT0805 body2.00+/-.10 x1.25+/-.10 x.50+/-.10 mm, terminations.35+/-.20 mm. Land outer span3.05 mm, inner gap1.05 mm, adequate lead overlap even at length/termination extremes. Nonpolar.',
 'PTFR0603':'Manufacturer a=3.0+/-.2,b=1.2+/-.2,c=1.0+/-.2 mm. Chosen a2.8,b1.2,c1.0: pads.9 x1.2 at+/-.95. Body maximum1.8x1.0x.5 mm. All six references use the qualified pattern, including package-identical replacements.',
 'C152_C154_C165':'Same CGA3 E body1.6+/-.1 x.8+/-.1 x.8+/-.1 mm; 220 nF,50 V,X7R,10%, nonpolar. Exact T0Y0N MPN retained in all active properties. Existing 0603 lands/models and pin identities preserved; no new DC-bias or voltage-rating credit is taken.',
 'U101':'HMS8 #PBF is 8-pin MSOP H-grade, -40..125 C. Same pin geometry/net assignment as prior HMS8 #WTRPBF. Retained KiCad MSOP8 generic lands/model are checked against MS8 body3.0+/-.102 mm, leadspan4.9+/-.152 mm, pitch.65 mm and maxheight1.1 mm; land pattern is a generic compatible pattern, not claimed identical to ADI recommendation. Owner accepts loss of #W controlled-manufacturing pedigree.'}
 out=dict(status='PASS_DESKTOP_PACKAGE_PAD_NET_STENCIL_AND_MODEL_SCREEN',source_PCB_sha256=sha(CAD/'GR86_CCA_RevB.kicad_pcb'),changed_refs=len(rows),rows=rows,manufacturer_evidence=index,engineering_basis=notes,native_DRC_findings=0,exact_vendor_3D_models_claimed=False,assembly_validation_performed=False,physical_tests=0)
 (D/'PACKAGE_QUALIFICATION.json').write_text(json.dumps(out,indent=2)+'\n');print('Package checks passed:',len(rows))
if __name__=='__main__':main()
