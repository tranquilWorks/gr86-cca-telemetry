#!/usr/bin/env python3
"""Regenerate I32 assembly and manufacturing deliverables from verified native CAD."""
from pathlib import Path
import csv,hashlib,json,math,shutil,sys,zipfile
D=Path(__file__).resolve().parent;W=D.parents[2];CAD=W/'candidate/cad';OUT=W/'current/i32_manufacturing'
sys.path.insert(0,str(W/'analyses/convergence_01/support'))
import check_combined_copper as c
from apply_redline import SPEC

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def put(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
def csvwrite(p,fields,rows):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',newline='')as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(rows)
def main():
    n=D/'native_final';nr=read(n/'RESULT.json');audit=read(D/'SOURCE_AUDIT.json')
    assert nr['status']=='NATIVE_OUTPUTS_COMPLETE'and nr['native_report_finding_count']==0
    assert nr['inputs_unchanged']and all(v['pass']for v in nr['output_postconditions'].values())
    for name,digest in nr['inputs']['cad'].items():assert sha(CAD/name)==digest,name
    for name,spec in read(n/'OUTPUT_MANIFEST.json')['files'].items():assert sha(n/name)==spec['sha256'],name
    b=c.sx.loads((CAD/'GR86_CCA_RevB.kicad_pcb').read_text());fps={c.prop(f)['Reference']:f for f in c.child(b,'footprint')}
    rows=list(csv.DictReader((n/'REVIEW_BOM.csv').open()));by={r['Reference']:r for r in rows};fitted=set(read(CAD/'FITTED_REFERENCES.json')['fitted_references'])
    assert len(rows)==len(by)==len(fitted)==177 and set(by)==fitted
    local={'F101','U401'};factory=fitted-local;dnp={r for r,f in fps.items()if c.prop(f).get('Assembly')=='DNP'}
    assert len(factory)==175 and dnp=={'C203','R301','R306'}
    for ref,row in by.items():
        p=c.prop(fps[ref]);assert row['Quantity']=='1'
        assert all(row[k]==p.get(k,'')for k in ['Value','MPN','LCSC','Manufacturer'])
        assert row['Footprint']==str(fps[ref][1])
    for ref,s in SPEC.items():assert by[ref]['MPN']==s['MPN']and by[ref]['LCSC']==s['LCSC'] and ref in factory
    old=read(D/'AUTHORED_REDLINE.json')['before'];old_mpns={x['properties']['MPN']for x in old.values()}
    assert not [(r,v['MPN'])for r,v in by.items()if v['MPN']in old_mpns]
    positions=list(csv.DictReader((n/'REVIEW_POSITIONS.csv').open()));pr={r['Ref']:r for r in positions};assert len(pr)==len(positions)==175 and set(pr)==factory
    origin=c.get(c.child(b,'setup')[0],'aux_axis_origin',[0,0]);checked=[]
    for ref,p in pr.items():
        f=fps[ref];x,y,*angle=c.get(f,'at');angle=angle[0]if angle else 0;side='top'if c.get(f,'layer')==['F.Cu']else'bottom'
        assert p['Side']==side and p['Val']==c.prop(f)['Value'] and p['Package']==str(f[1]).split(':',1)[1]
        assert abs(float(p['PosX'])-(x-origin[0]))<.0000011
        assert abs(float(p['PosY'])-(origin[1]-y))<.0000011
        assert abs((float(p['Rot'])-angle+180)%360-180)<.000001
        if ref in SPEC:checked.append(dict(ref=ref,board_X_mm=x,board_Y_mm=y,side=side,native_rotation_deg=float(p['Rot']),CPL_X_mm=float(p['PosX']),CPL_Y_mm=float(p['PosY'])))
    fields=list(rows[0]);key=lambda r:(''.join(filter(str.isalpha,r)),int(''.join(filter(str.isdigit,r))))
    A=OUT/'assembly'
    csvwrite(A/'COMPLETE_FITTED_BOM.csv',fields,[by[r]for r in sorted(fitted,key=key)])
    csvwrite(A/'LOCAL_ASSEMBLY_BOM.csv',fields,[by[r]for r in sorted(local,key=key)])
    csvwrite(A/'JLCPCB_BOM.csv',['Comment','Designator','Footprint','LCSC Part #','MPN','Manufacturer'],[dict(Comment=by[r]['Value'],Designator=r,Footprint=by[r]['Footprint'],**{'LCSC Part #':by[r]['LCSC']},MPN=by[r]['MPN'],Manufacturer=by[r]['Manufacturer'])for r in sorted(factory,key=key)])
    missing=[by[r]for r in sorted(factory,key=key)if not by[r]['LCSC']]
    csvwrite(A/'SOURCING_REQUIRED.csv',fields,missing)
    csvwrite(A/'JLCPCB_CPL.csv',['Designator','Mid X','Mid Y','Layer','Rotation'],[{'Designator':r,'Mid X':pr[r]['PosX']+'mm','Mid Y':pr[r]['PosY']+'mm','Layer':pr[r]['Side'].title(),'Rotation':pr[r]['Rot']}for r in sorted(factory,key=key)])
    assert set(read(A/'DO_NOT_POPULATE.json'))==dnp
    # Regenerate all native layer/drill/job exports, keeping the same 49 vias.
    fab=OUT/'fabrication';g=fab/'gerbers';g.mkdir(parents=True,exist_ok=True)
    source_gerbers={p.name:p for p in(n/'review_gerbers').iterdir()if p.is_file()};assert len(source_gerbers)==14
    assert {p.name for p in g.iterdir()if p.is_file()}==set(source_gerbers)
    for name,p in source_gerbers.items():shutil.copyfile(p,g/name)
    with zipfile.ZipFile(fab/'JLCPCB_GERBERS.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9)as z:
        for p in sorted(g.iterdir()):z.write(p,p.name)
    vip=audit['filled_capped_planarized_vias'];assert len(vip)==49
    csvwrite(fab/'FILL_CAP_PLANARIZE_49_VIAS.csv',['Reference','UUID','PCB X mm','PCB Y mm','Drill mm','Land mm'],[dict(zip(['Reference','UUID','PCB X mm','PCB Y mm','Drill mm','Land mm'],[v['reference'],v['uuid'],*v['xy'],v['drill'],v['land']]))for v in vip])
    assert read(fab/'STACKUP_AND_PROCESS.json')['filled_capped_planarized_vias']==49
    for src,dest in [('REVIEW_SCHEMATIC.pdf','documentation/SCHEMATIC.pdf'),('REVIEW_COMPONENTS.step','documentation/POPULATED_COMPONENTS.step'),('PCB_NETLIST.d356','fabrication/PCB_NETLIST.d356'),('SCHEMATIC_NETLIST.xml','documentation/SCHEMATIC_NETLIST.xml')]:
        p=OUT/dest;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(n/src,p)
    # A complete current editable copy; external standard model digests are in
    # native/MODEL_RESOLUTION.json. No unrelated firmware recompile is claimed.
    for name,digest in nr['inputs']['cad'].items():
        p=OUT/'editable_source/cad'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(CAD/name,p);assert sha(p)==digest
    fw=W/'analyses/i32/recovery_20260914/firmware_160mhz'
    put(OUT/'FIRMWARE_EFFECTIVITY.json',dict(status='UNCHANGED_SOURCE_REUSES_VERIFIED_160MHZ_RECOVERY_BUILD',evidence=str(fw.relative_to(W)),source_files=audit['firmware_files'],release_check=read(fw/'RELEASE_CHECK.json'),flashed=False,target_execution=False))
    result=dict(status='PASS_NATIVE_SOURCE_BOM_CPL_MANUFACTURING_BINDING',source_PCB_sha256=audit['source_PCB_sha256'],filled_PCB_sha256=audit['filled_PCB_sha256'],native_schematic_XML_sha256=sha(n/'SCHEMATIC_NETLIST.xml'),native_postconditions=len(nr['output_postconditions']),fitted=177,factory_CPL_rows=175,local_install=sorted(local),DNP=sorted(dnp),frozen_changed_refs=len(SPEC),frozen_MPN_Cnumber_binding=True,old_frozen_MPNs_in_active_BOM=0,other_unchanged_factory_refs_without_LCSC=len(missing),unchanged_unassigned_refs=[r['Reference']for r in missing],aux_drill_origin_mm=origin,changed_CPL=checked,gerber_layers=11,drill_files=2,gerber_job_files=1,special_vias=49,stock_or_capacity_reserved=False,physical_tests=0,L121_process='JLC catalog manualWeld/wave handling; supplier process approval required. Remains factory supplied, not a third local-install exception.')
    put(D/'MANUFACTURING_RECONCILIATION.json',result)
    manifest=dict(schema_version=1,**result,excludes=['SOURCE_MANIFEST.json'],files={str(p.relative_to(OUT)):dict(sha256=sha(p),bytes=p.stat().st_size)for p in sorted(OUT.rglob('*'))if p.is_file()and p.name!='SOURCE_MANIFEST.json'})
    put(OUT/'SOURCE_MANIFEST.json',manifest)
    with zipfile.ZipFile(W/'product/GR86_I32_PROCUREMENT_REDLINE.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9)as z:
        for p in sorted(OUT.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(OUT))
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
