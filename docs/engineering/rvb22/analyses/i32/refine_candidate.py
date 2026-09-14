#!/usr/bin/env python3
"""Apply the coordinated transient repair to the hash-identified 170-part I32 checkpoint.

This is an authoring step, not verification. The saved candidate is authoritative;
rerun routing, finishing, native checks and source-bound analyses after this step.
"""
from pathlib import Path
import copy,hashlib,json,tempfile
import pcbnew as k
import author_candidate as a
import route_candidate as r
c=a.c
INPUT_SHA='44c98f6ab4153a8f0c2d6d99dea482617dc97870ac98be0e082ddb5c0976a967'
PARTS=copy.deepcopy(a.PARTS)
CAPS=['C162','C163','C164','C166','C167','C168']
for i,ref in enumerate(CAPS):
    PARTS[ref]=dict(copy.deepcopy(a.PARTS['C162']),pcb=[15.9+5.6*i,-5,90,'F.Cu'],sch=[45+65*i,377])
for ref,xy in {'R160':(48.3,-8),'R161':(51.7,-8),'R162':(48.3,-5.5),'R163':(51.7,-5.5),'R159':(48.3,-2.5),'C165':(51.7,-2.5),'TP154':(54,-.5)}.items():
    PARTS[ref]['pcb']=[*xy,0,'F.Cu']
PARTS['R159'].update(mpn='CRCW060347K0FKEA',value='47k /1% PG PULLUP')
PARTS['C159'].update(mpn='CGA4F2C0G1H153J085AA',value='15n /50V C0G 5% CT',fp='RevB:C_0805_2012Metric',pcb=[46.2,2.8,0,'B.Cu'],url='https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=CGA4F2C0G1H153J085AA')
PARTS['C165']['sch']=[449.58,355.6]
for ref,xy,sch,nets in [('R166',(37.8,7.6),(449.58,258),{'1':'3V3_ENABLE','2':'3V3_BUCK_ENABLE'}),('R167',(43.5,8.3),(533.4,279.4),{'1':'3V3_BUCK_ENABLE','2':'GND'})]:
    PARTS[ref]=dict(copy.deepcopy(a.PARTS['R159']),mpn='CRCW0603330KFKEA',value='330k /1% U151 EN DIVIDER',pcb=[*xy,0,'B.Cu'],sch=list(sch),nets=nets)
CHANGES={
 'C206':{'MPN':'T598X687M006ATE025','Value':'680u /6.3V POLYMER','Capacitance_Condition':'Ceff>=304.64uF stacked; <=3.78V steady at125C'},
 'R155':{'MPN':'TNPU060311K8HWEA00','Value':'11.8k /0.02% 2ppm FB TOP','Datasheet':'https://www.vishay.com/docs/28779/tnpu-e3.pdf'},
 'R156':{'MPN':'TNPU06035K05HWEA00','Value':'5.05k /0.02% 2ppm FB BOTTOM','Datasheet':'https://www.vishay.com/docs/28779/tnpu-e3.pdf'},
 'R158':{'MPN':'WSL2512R3300FEA','Value':'330m /1% BULK DAMPING'},
}
REMOVED_TASKS={
 'isolation_slew_cap','iso_ground_ct','iso_input_bulk_local','iso_input_bulk_parallel','third_input_bulk','iso_sns_vin',
 'sns_divider_via','sns_divider','sns_to_via','sns_inner','iso_en_divider','iso_en_tp','iso_en_remote_via','iso_en_tp_via','iso_en_inner',
 'iso_en_supply','pg_supply','pg_to_via','u151_en_local','u151_en_cap_via','u151_en_cap','u151_en_cap_inner',
 'c162_ground_via','c162_ground','c163_ground_via','c163_ground','c164_ground_via','c164_ground',
 'r161_ground_via','r161_ground','r163_ground_via','r163_ground','c165_ground_via','c165_ground',
}

def main():
    assert k.GetBuildVersion().startswith('9.0.9')
    assert hashlib.sha256(r.P.read_bytes()).hexdigest()==INPUT_SHA
    schpath=a.CAD/'Power_3V3.kicad_sch';sch=c.sx.loads(schpath.read_text())
    syms={c.prop(x)['Reference']:x for x in c.child(sch,'symbol')}
    path=c.child(c.child(c.child(syms['R155'],'instances')[0],'project')[0],'path')[0][1]
    moved=set(CAPS)|{'R159','R160','R161','R162','R163','C165','TP154','C159','R166','R167'}
    for ref in moved:
        p=PARTS[ref];old=syms.get(ref);template=old or syms['C162'if ref.startswith('C')else'R159']
        if old is not None:sch.remove(old)
        inst=a.instance(template,ref,p,path)
        if ref in CAPS:
            a.prop(inst,'Height','4.3mm maximum');a.prop(inst,'Polarity','Positive terminal1; negative terminal2');a.prop(inst,'Capacitance_Condition','Ceff>=210.56uF each stacked engineering bound through125C')
        if ref=='C159':a.prop(inst,'Height','1.0mm maximum')
        sch.append(inst)
        for n in p['nets']:
            ident=a.uid(ref+'wire'+n)
            for oldwire in list(c.child(sch,'wire')):
                if c.get(oldwire,'uuid')==[ident]:
                    ends=[q[1:]for q in c.child(c.child(oldwire,'pts')[0],'xy')]
                    for lab in list(c.child(sch,'global_label')):
                        if c.get(lab,'at')[:2]in ends:sch.remove(lab)
                    sch.remove(oldwire)
        x,y=p['sch']
        for n in p['nets']:
            at=(x,y if ref.startswith('TP')else y+(-3.81 if n=='1'else 3.81));end=(x-7.62,at[1])
            sch.append(a.wire(at,end,ref+'wire'+n));sch.append(a.label(p['nets'][n],*end))
    for lab in c.child(sch,'global_label'):
        if c.get(lab,'at')[:2]==[111.76,109.22]:lab[1]='3V3_BUCK_ENABLE'
    for sym in c.child(sch,'symbol'):
        for key,val in CHANGES.get(c.prop(sym).get('Reference'),{}).items():a.prop(sym,key,val)
    for tx in c.child(sch,'text'):
        if tx[1].startswith('I32: source setpoint'):
            tx[1]='I32: 3.336634V source (11.8k/5.05k), 400kHz FPWM. C206680uF/6.3V, R158330mOhm.\nSix 470uF/10V input capacitors supply cold750mA startup; C15915nF limits their inrush.\nR166/R167 divide PG for U151 EN: Q153 is fully on before U151 starts.\nSee I32 source-bound evidence and physical correlation gates.'
        if tx[1].startswith('I32 ISOLATION:'):
            tx[1]='I32 ISOLATION: TPS22953 (no QOD). R162/R163 enable the isolator; SNS monitors its output.\nPG/C165 drive Q153; R166/R167 divide PG for U151 EN.\nC162/C163/C164/C166/C167/C168 total2820uF nominal,1263.36uF minimum.\nR151 remains the upstream isolation link. Sustained release load remains450mA.'
    schpath.write_text(a.dump(sch))
    b=k.LoadBoard(str(r.P));net=k.NETINFO_ITEM(b,'3V3_BUCK_ENABLE');b.Add(net)
    nets={str(n):b.FindNet(str(n))for n in b.GetNetsByName()}
    fps={f.GetReference():f for f in b.GetFootprints()}
    for ref in moved:
        p=PARTS[ref];old=fps.get(ref)
        fp=k.FootprintLoad(str(a.CAD/'libraries/RevB.pretty'),p['fp'].split(':')[1]);assert fp
        b.Add(fp)
        if p['pcb'][3]=='B.Cu':fp.Flip(k.VECTOR2I(0,0),False)
        fp.SetReference(ref);fp.SetValue(p['value']);fp.SetFPID(k.LIB_ID('RevB',p['fp'].split(':')[1]))
        fp.SetOrientationDegrees(p['pcb'][2]);fp.SetPosition(k.VECTOR2I(k.FromMM(p['pcb'][0]),k.FromMM(p['pcb'][1])))
        # The schematic and board share deterministic identifiers.
        fp.SetPath(k.KIID_PATH(path+'/'+a.uid(ref+'-symbol')))
        for pad in fp.Pads():
            n=pad.GetNumber()
            if n:pad.SetNet(nets[p['nets'][n]])
        if ref in CAPS:
            fp.Models().clear()
            for model in fps['C206'].Models():fp.Models().append(model)
        if ref.startswith('TP'):fp.SetAttributes(k.FP_EXCLUDE_FROM_POS_FILES|k.FP_EXCLUDE_FROM_BOM)
        if old is not None:b.Remove(old)
    for f in b.GetFootprints():
        for key,val in CHANGES.get(f.GetReference(),{}).items():
            if key=='Value':f.SetValue(val)
        if f.GetReference()=='U151':next(p for p in f.Pads()if p.GetNumber()=='11').SetNet(nets['3V3_BUCK_ENABLE'])
    k.SaveBoard(str(r.P),b)
    tree=c.sx.loads(r.P.read_text());removed=[]
    for f in c.child(tree,'footprint'):
        ref=c.prop(f).get('Reference')
        if ref not in moved:continue
        a.setv(f,'uuid',[a.uid(ref+'footprint')])
        p=PARTS[ref]
        for key,val in {'MPN':p['mpn'],'Manufacturer':p['manufacturer'],'Datasheet':p['url'],'Assembly':'BARE PCB'if ref.startswith('TP')else'FACTORY','Qualification':'I32 source-bound candidate; physical qualification required'}.items():a.prop(f,key,val)
        if ref in CAPS:
            a.prop(f,'Height','4.3mm maximum');a.prop(f,'Polarity','Positive terminal1; negative terminal2');a.prop(f,'Capacitance_Condition','Ceff>=210.56uF each stacked engineering bound through125C')
        if ref=='C159':a.prop(f,'Height','1.0mm maximum')
        for pad in c.child(f,'pad'):
            if pad[1]:a.setv(pad,'uuid',[a.uid(ref+'-pad-'+str(pad[1]))])
    for f in c.child(tree,'footprint'):
        for key,val in CHANGES.get(c.prop(f).get('Reference'),{}).items():a.prop(f,key,val)
    ids={r.uid(t+':'+str(i))for t in REMOVED_TASKS for i in range(2000)}|{r.uid(t)for t in REMOVED_TASKS}
    for q in list(tree):
        if c.tag(q)in ['segment','via']and c.get(q,'uuid')[0]in ids:removed.append(c.get(q,'uuid')[0]);tree.remove(q)
    r.P.write_text(r.dump(tree))
    inv=json.loads((a.CAD/'FITTED_REFERENCES.json').read_text());inv['fitted_references']=sorted(set(inv['fitted_references'])|{'C166','C167','C168','R166','R167'});inv['I32_expected_count']=len(inv['fitted_references']);inv['I32_added_references']=sorted(set(inv['I32_added_references'])|{'C166','C167','C168','R166','R167'});(a.CAD/'FITTED_REFERENCES.json').write_text(json.dumps(inv,indent=2)+'\n')
    (a.HERE/'TRANSIENT_REFINEMENT.json').write_text(json.dumps(dict(input_PCB_sha256=INPUT_SHA,parts={ref:PARTS[ref]for ref in sorted(moved)},property_changes=CHANGES,removed_copper_uuids=removed,status='STAGED_REQUIRES_ROUTING_AND_VERIFICATION'),indent=2)+'\n')
    print('Staged',inv['I32_expected_count'],'fitted; removed',len(removed),'obsolete route elements')

if __name__=='__main__':main()
