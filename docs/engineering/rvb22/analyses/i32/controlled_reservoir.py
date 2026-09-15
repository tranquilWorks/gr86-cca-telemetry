#!/usr/bin/env python3
"""Stage the selected I32 reservoir sequencer from exact verified 170-part inputs.

Authoring only: routing, native parity, mechanics, thermal and source binding
must follow. The rejected six-capacitor variant is not the input to this step.
"""
from pathlib import Path
import copy,hashlib,json
import pcbnew as k
import author_candidate as a
import route_candidate as r
c=a.c
INPUT_SHA='44c98f6ab4153a8f0c2d6d99dea482617dc97870ac98be0e082ddb5c0976a967'
INPUT_SCH_SHA='e33c5a4e309fe20f8d03f9140058b96ad3b9a760f0d76c29cd8a0209b4204f6e'
PARTS=copy.deepcopy(a.PARTS)
for ref in ['C163','C164']:PARTS.pop(ref)
CT_MPN='CGA4J1C0G2A333J125AE'
PARTS['C159'].update(mpn=CT_MPN,value='33n /100V C0G 5% CT',fp='RevB:TDK_CGA4J1_33N_I32',pcb=[44.3,.7,0,'B.Cu'],url='https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no='+CT_MPN)
PARTS['C162']['sch']=[45.72,377.19]
for ref,xy in {'R164':[449.58,335.28],'C161':[449.58,360.68],'R165':[508,355.6],'C165':[368.3,400.05]}.items():PARTS[ref]['sch']=xy
PARTS['R159'].update(mpn='CRCW060347K0FKEA',value='47k /1% PG PULLUP')
for ref,mpn,value in [('R160','TNPU06036K34HWEA00','6.34k /0.02% SNS TOP'),('R161','TNPU06031K00HWEA00','1k /0.02% SNS BOTTOM'),('R162','TNPU06034K70HWEA00','4.7k /0.02% ISO EN TOP'),('R163','TNPU06031K00HWEA00','1k /0.02% ISO EN BOTTOM')]:
    PARTS[ref].update(mpn=mpn,value=value,url='https://www.vishay.com/docs/28779/tnpu-e3.pdf')
for ref,xy,sch,nets in [('R166',(35,-7.5),(449.58,257.81),{'1':'3V3_ENABLE','2':'3V3_BUCK_ENABLE'}),('R167',(39,-7.5),(533.4,279.4),{'1':'3V3_BUCK_ENABLE','2':'GND'})]:
    PARTS[ref]=dict(copy.deepcopy(a.PARTS['R159']),mpn='CRCW0603330KFKEA',value='330k /1% U151 EN DIVIDER',pcb=[*xy,0,'F.Cu'],sch=list(sch),nets=nets)
PARTS['U153']=dict(copy.deepcopy(PARTS['U152']),value='TPS22953-Q1 BULK CHARGER',pcb=[79.1,-3.5,0,'B.Cu'],sch=[205.74,370.84],nets={'1':'+3V3','2':'+3V3','3':'+3V3','4':'3V3_BULK_ENABLE','5':'GND','6':'3V3_BULK_CT','7':'unconnected-(U153-PG-Pad7)','8':'+3V3','9':'3V3_BULK_SWITCHED','10':'3V3_BULK_SWITCHED','11':'GND'})
PARTS['C166']=dict(copy.deepcopy(PARTS['C159']),pcb=[85.85,-3.0,90,'B.Cu'],sch=[284.48,381],nets={'1':'3V3_BULK_CT','2':'GND'})
PARTS['C167']=dict(copy.deepcopy(PARTS['C161']),mpn='GCM188R71C105KA64D',value='1u /16V X7R BULK INPUT',pcb=[78.5,-.4,0,'B.Cu'],sch=[111.76,355.6],nets={'1':'+3V3','2':'GND'},url='https://www.murata.com/en-us/products/productdetail?partno=GCM188R71C105KA64D')
for ref,mpn,value,xy,sch,nets in [
 ('R168','CRCW06031K00FKEA','1k /1% RESERVOIR BLEED',(86.35,2.0),(368.3,377.19),{'1':'3V3_BULK_DAMPED','2':'GND'}),
 ('R169','TNPU06033K01HWEA00','3.01k /0.02% BULK EN TOP',(80,2.0),(45.72,350.52),{'1':'+3V3','2':'3V3_BULK_ENABLE'}),
 ('R170','TNPU06031K00HWEA00','1k /0.02% BULK EN BOTTOM',(83.3,2.0),(111.76,400.05),{'1':'3V3_BULK_ENABLE','2':'GND'}),
 ('R204','CRCW0603100KFKEA','100k /1% RESET DELAY',(75.6,6.9),(50.8,215.9),{'1':'+3V3','2':'SUP_RESET_DELAY'})]:
    PARTS[ref]=dict(copy.deepcopy(a.PARTS['R159']),mpn=mpn,value=value,pcb=[*xy,0,'B.Cu'],sch=list(sch),nets=nets)
    if ref in ['R169','R170']:PARTS[ref]['url']='https://www.vishay.com/docs/28779/tnpu-e3.pdf'
    if ref=='R204':
        PARTS[ref]['sheet']='ESP32.kicad_sch';PARTS[ref]['pcb'][2]=90
CHANGES={
 'C206':{'MPN':'T598X687M006ATE025','Value':'680u /6.3V POLYMER','Capacitance_Condition':'304.64uF minimum,1432.08uF maximum stacked envelope; <=3.78V steady at125C'},
 'R155':{'MPN':'TNPU060311K8HWEA00','Value':'11.8k /0.02% 2ppm FB TOP','Datasheet':'https://www.vishay.com/docs/28779/tnpu-e3.pdf'},
 'R156':{'MPN':'TNPU06035K05HWEA00','Value':'5.05k /0.02% 2ppm FB BOTTOM','Datasheet':'https://www.vishay.com/docs/28779/tnpu-e3.pdf'},
 'R158':{'MPN':'WSL2512R3000FEA','Value':'300m /1% BULK DAMPING'},
}
REMOVE_REFS={'C163','C164'}
NEW_REFS={'U153','C166','C167','R166','R167','R168','R169','R170','R204'}
REPLACE_REFS={'C159','R159','C162'}|NEW_REFS
REMOVED_TASKS={'iso_input_bulk_local','iso_input_bulk_parallel','third_input_bulk','c163_ground_via','c163_ground','c164_ground_via','c164_ground','isolation_slew_cap','iso_ground_ct','u151_en_local','bulk_feed','bulk_cap_via','bulk_damper_to_via','bulk_via_to_cap'}

def remove_wires(sch,ref):
    for n in range(1,12):
        ident=a.uid(ref+'wire'+str(n))
        for w in list(c.child(sch,'wire')):
            if c.get(w,'uuid')!=[ident]:continue
            ends=[q[1:]for q in c.child(c.child(w,'pts')[0],'xy')]
            for label in list(c.child(sch,'global_label')):
                if c.get(label,'at')[:2]in ends:sch.remove(label)
            sch.remove(w)

def main():
    assert k.GetBuildVersion().startswith('9.0.9')
    assert hashlib.sha256(r.P.read_bytes()).hexdigest()==INPUT_SHA
    assert hashlib.sha256((a.CAD/'Power_3V3.kicad_sch').read_bytes()).hexdigest()==INPUT_SCH_SHA
    # TDK's soft-termination maximum body and recommended reflow pads, not a
    # generic0805 nominal body: PA1.10, PB0.90, PC1.20mm.
    fp=c.sx.loads((a.CAD/'libraries/RevB.pretty/C_0805_2012Metric.kicad_mod').read_text());fp[1]='TDK_CGA4J1_33N_I32'
    for q in list(fp):
        if c.tag(q)in ['model','fp_rect','fp_line']:fp.remove(q)
    for pad in c.child(fp,'pad'):
        a.setv(pad,'at',[-1.0 if pad[1]=='1'else 1.0,0]);a.setv(pad,'size',[.9,1.2])
    for layer,xx,yy in [('F.Fab',1.225,.75),('F.CrtYd',1.7,1.0)]:
        fp.append(a.parse(f'(fp_rect (start {-xx} {-yy}) (end {xx} {yy}) (stroke (width .05) (type default)) (fill none) (layer "{layer}"))'))
    fp.append(a.parse('(model "${KIPRJMOD}/models/ENVELOPE_TDK_CGA4J1_33N_I32.step" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))'))
    (a.CAD/'libraries/RevB.pretty/TDK_CGA4J1_33N_I32.kicad_mod').write_text(a.dump(fp))
    sheets={name:c.sx.loads((a.CAD/name).read_text())for name in ['Power_3V3.kicad_sch','ESP32.kicad_sch']}
    for name,sch in sheets.items():
        symbols={c.prop(x)['Reference']:x for x in c.child(sch,'symbol')}
        path=c.child(c.child(c.child(next(iter(symbols.values())),'instances')[0],'project')[0],'path')[0][1]
        for ref in REMOVE_REFS:
            if ref in symbols:sch.remove(symbols[ref]);remove_wires(sch,ref)
        for ref in sorted(REPLACE_REFS):
            p=PARTS[ref]
            if p.get('sheet','Power_3V3.kicad_sch')!=name:continue
            old=symbols.get(ref)
            template=old or symbols['U152'if ref=='U153'else 'C152'if ref.startswith('C')else 'R203'if name.startswith('ESP')else 'R155']
            if old is not None:sch.remove(old)
            remove_wires(sch,ref)
            sym=a.instance(template,ref,p,path);sch.append(sym);p['sheet_path']=path
            if ref in ['C159','C166']:a.prop(sym,'Height','1.50mm maximum')
            if ref=='U153':
                for key,dy in [('Reference',-24),('Value',-21)]:
                    q=next(q for q in c.child(sym,'property')if q[1]==key);a.setv(q,'at',[p['sch'][0],p['sch'][1]+dy,0])
            x,y=p['sch'];defs=a.PIN_DEFS if ref=='U153'else [('1','','',0,3.81,0),('2','','',0,-3.81,0)]
            for n,_,_,dx,dy,ang in defs:
                at=(round(x+dx,5),round(y-dy,5))
                if ref=='U153'and n=='7':
                    sch.append(a.parse(f'(no_connect (at {at[0]} {at[1]}) (uuid "{a.uid("U153-PG-NC")}"))'));continue
                end=(round(at[0]+(7.62 if dx>0 else -7.62),5),at[1]);sch.append(a.wire(at,end,ref+'wire'+n));sch.append(a.label(p['nets'][n],*end,180 if dx>0 else 0))
        for sym in c.child(sch,'symbol'):
            for key,val in CHANGES.get(c.prop(sym).get('Reference'),{}).items():a.prop(sym,key,val)
            ref=c.prop(sym).get('Reference')
            if ref in ['R160','R161','R162','R163']:
                for key,val in {'MPN':PARTS[ref]['mpn'],'Value':PARTS[ref]['value'],'Datasheet':PARTS[ref]['url']}.items():a.prop(sym,key,val)
        if name.startswith('Power'):
            for label in c.child(sch,'global_label'):
                if c.get(label,'at')[:2]==[111.76,109.22]:label[1]='3V3_BUCK_ENABLE'
                if label[1]=='+3V3'and c.get(label,'at')[:2]==[294.64,285.75]:label[1]='3V3_BULK_SWITCHED'
            # R158's existing pin1 wire endpoint determines the exact old label.
            r158=symbols['R158'];x,y,*_=c.get(r158,'at')
            wires=[w for w in c.child(sch,'wire')if [x,y-3.81]in[q[1:]for q in c.child(c.child(w,'pts')[0],'xy')]]
            ends=[q[1:]for w in wires for q in c.child(c.child(w,'pts')[0],'xy')]
            labels=[lab for lab in c.child(sch,'global_label')if c.get(lab,'at')[:2]in ends]
            assert len(labels)==1;labels[0][1]='3V3_BULK_SWITCHED'
            for tx in c.child(sch,'text'):
                if tx[1].startswith('I32:'):
                    tx[1]='I32: 3.336634V source (11.8k/5.05k),400kHz FPWM. C206680uF/6.3V; R158300mOhm.\nU153 slews only C206; U202 reset waits180-420ms via R204. Main750mA cold-start stress retained.\nC162470uF/10V supplies isolated VIN; C159/C16633nF C0G control independent charging.\nU152/Q152/Q153 mitigate reverse discharge. See source-bound evidence and physical gates.'
                if tx[1].startswith('I32 ISOLATION:'):
                    tx[1]='I32: U152 TPS22953 (no QOD). SNS monitors VIN; PG/C165 drive Q153.\nR166/R167 divide PG for U151 EN. C162470uF input reservoir.\nU153 SNS follows its main input; PG unused. R168 drains isolated C206.\nSustained I25 profile and fixed release heat allocation remain unchanged.'
                if tx[1].startswith('RVB22 — ADJUSTABLE'):tx[1]='I32 — COORDINATED3.336634V POWER AND RESERVOIR SEQUENCING'
        else:
            u=symbols['U202'];lib=next(q for q in c.child(c.child(sch,'lib_symbols')[0],'symbol')if q[1]==c.get(u,'lib_id')[0]);pin=next(p for ss in c.child(lib,'symbol')for p in c.child(ss,'pin')if c.get(p,'number')[0]=='4')
            ux,uy,*_=c.get(u,'at');px,py,*_=c.get(pin,'at');at=[round(ux+px,5),round(uy-py,5)]
            nc=[q for q in c.child(sch,'no_connect')if c.get(q,'at')==at];assert len(nc)==1;sch.remove(nc[0])
            end=[at[0]+7.62,at[1]];sch.append(a.wire(at,end,'U202-delay'));sch.append(a.label('SUP_RESET_DELAY',*end,180))
            for tx in c.child(sch,'text'):
                if tx[1].startswith('RVB22 RESET:'):
                    tx[1]='I32 RESET: U202 falling3.023950-3.116050V; release threshold max3.193952V.\nR204100k ties CT toVDD: published180-420ms delay permits C206 charging before boot.\nC203 remains DNP. Normal rail transients must stay>3.116050V and<3.6V without reset.\nRetain programmer open-drain reset; hold GPIO0 until actual EN release.\nPhysical startup/boot/reset and RevA fault correlation remain acceptance gates.'
        (a.CAD/name).write_text(a.dump(sch))
    b=k.LoadBoard(str(r.P));fps={f.GetReference():f for f in b.GetFootprints()}
    allnets={v for ref in NEW_REFS for v in PARTS[ref]['nets'].values()}
    for name in allnets:
        if b.FindNet(name) is None:b.Add(k.NETINFO_ITEM(b,name))
    nets={str(n):b.FindNet(str(n))for n in b.GetNetsByName()}
    for ref in sorted((REPLACE_REFS-{'C162','R159'})|{'R158'}):
        old=fps.get(ref)
        if ref=='R158':
            old.SetOrientationDegrees(90);old.SetPosition(k.VECTOR2I(k.FromMM(82.7),k.FromMM(-4)));next(p for p in old.Pads()if p.GetNumber()=='1').SetNet(nets['3V3_BULK_SWITCHED']);continue
        p=PARTS[ref];fp=k.FootprintLoad(str(a.CAD/'libraries/RevB.pretty'),p['fp'].split(':')[1]);assert fp;b.Add(fp)
        if p['pcb'][3]=='B.Cu':fp.Flip(k.VECTOR2I(0,0),False)
        fp.SetReference(ref);fp.SetValue(p['value']);fp.SetFPID(k.LIB_ID('RevB',p['fp'].split(':')[1]));fp.SetOrientationDegrees(p['pcb'][2]);fp.SetPosition(k.VECTOR2I(k.FromMM(p['pcb'][0]),k.FromMM(p['pcb'][1])));fp.SetPath(k.KIID_PATH(p['sheet_path']+'/'+a.uid(ref+'-symbol')))
        for pad in fp.Pads():
            if pad.GetNumber():pad.SetNet(nets[p['nets'][pad.GetNumber()]])
        if old is not None:b.Remove(old)
    for ref in REMOVE_REFS:b.Remove(fps[ref])
    for ref,pin,net in [('U151','11','3V3_BUCK_ENABLE'),('U202','4','SUP_RESET_DELAY')]:next(p for p in fps[ref].Pads()if p.GetNumber()==pin).SetNet(nets[net])
    fps['R159'].SetValue(PARTS['R159']['value'])
    for ref,props in CHANGES.items():fps[ref].SetValue(props['Value'])
    k.SaveBoard(str(r.P),b)
    tree=c.sx.loads(r.P.read_text())
    for f in c.child(tree,'footprint'):
        ref=c.prop(f).get('Reference')
        if ref in ['R160','R161','R162','R163']:
            for key,val in {'MPN':PARTS[ref]['mpn'],'Value':PARTS[ref]['value'],'Datasheet':PARTS[ref]['url']}.items():a.prop(f,key,val)
        if ref in REPLACE_REFS:
            p=PARTS[ref]
            for key,val in {'MPN':p['mpn'],'Manufacturer':p['manufacturer'],'Datasheet':p['url'],'Assembly':'FACTORY','Qualification':'I32 selected source; native evidence and physical gates control'}.items():a.prop(f,key,val)
            if ref in ['C159','C166']:a.prop(f,'Height','1.50mm maximum')
            if ref not in ['C162','R159']:
                a.setv(f,'uuid',[a.uid(ref+'footprint')])
                for pad in c.child(f,'pad'):
                    if pad[1]:a.setv(pad,'uuid',[a.uid(ref+'-pad-'+str(pad[1]))])
        for key,val in CHANGES.get(ref,{}).items():a.prop(f,key,val)
    ids={r.uid(t+':'+str(i))for t in REMOVED_TASKS for i in range(2000)}|{r.uid(t)for t in REMOVED_TASKS};removed=[]
    for q in list(tree):
        if c.tag(q)in ['segment','via']and c.get(q,'uuid')[0]in ids:removed.append(c.get(q,'uuid')[0]);tree.remove(q)
        if c.tag(q)=='gr_text'and c.get(q,'uuid')in [[a.uid(ref+'-polarity')]for ref in REMOVE_REFS]:tree.remove(q)
    r.P.write_text(r.dump(tree))
    inv=json.loads((a.CAD/'FITTED_REFERENCES.json').read_text());inv['fitted_references']=sorted((set(inv['fitted_references'])-REMOVE_REFS)|NEW_REFS);inv['I32_expected_count']=len(inv['fitted_references']);assert inv['I32_expected_count']==177
    inv['I32_added_references']=sorted((set(inv['I32_added_references'])-REMOVE_REFS)|NEW_REFS);(a.CAD/'FITTED_REFERENCES.json').write_text(json.dumps(inv,indent=2)+'\n')
    (a.HERE/'CONTROLLED_RESERVOIR_CHANGES.json').write_text(json.dumps(dict(input_PCB_sha256=INPUT_SHA,input_schematic_sha256=INPUT_SCH_SHA,parts=PARTS,property_changes=CHANGES,removed_refs=sorted(REMOVE_REFS),new_refs=sorted(NEW_REFS),removed_copper_uuids=removed,status='STAGED_REQUIRES_ROUTING_AND_VERIFICATION'),indent=2)+'\n')
    print('Staged177 fitted; removed',len(removed),'obsolete copper elements')

if __name__=='__main__':main()
