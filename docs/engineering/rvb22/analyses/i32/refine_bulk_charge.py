#!/usr/bin/env python3
"""Adopt the source-voltage correction's slower C206 charging on frozen I32 CAD.

This is the final 177-part refinement, following controlled_reservoir.py and its
native routing/finishing. It does not rerun a superseded 170-part authoring step.
"""
from pathlib import Path
import hashlib, json, copy
import pcbnew as k
import author_candidate as a
c=a.c
INPUT_SHA='56aa12528c6ee873235d2a1cabd6f6c738800f3424a57ef5b87702b930f36ab7'
MPN='CGA5L1C0G2A683J160AE'
VALUE='68n /100V C0G 5% BULK CT'
def main():
    assert k.GetBuildVersion().startswith('9.0.9')
    pcb=a.CAD/'GR86_CCA_RevB.kicad_pcb'
    assert hashlib.sha256(pcb.read_bytes()).hexdigest()==INPUT_SHA
    tree=c.sx.loads(pcb.read_text())
    f=next(f for f in c.child(tree,'footprint')if c.prop(f).get('Reference')=='C166')
    assert c.prop(f)['MPN']=='CGA4J1C0G2A333J125AE'
    before=copy.deepcopy(f)
    a.setv(f,'at',[85.85,-3,90])
    props={'Value':VALUE,'MPN':MPN,'Height':'1.90mm maximum','Datasheet':'https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no='+MPN}
    for key,value in props.items():a.prop(f,key,value)
    # TDK reflow PA2.20/PB1.10/PC1.50mm; maximum body3.60x1.90x1.90.
    for pad in c.child(f,'pad'):
        a.setv(pad,'at',[-1.65 if pad[1]=='1'else 1.65,0,90]);a.setv(pad,'size',[1.1,1.5])
    for q in c.child(f,'fp_rect'):
        layer=c.get(q,'layer')[0]
        if layer=='B.Fab':a.setv(q,'start',[-1.8,.95]);a.setv(q,'end',[1.8,-.95])
        elif layer=='B.CrtYd':a.setv(q,'start',[-2.45,1.2]);a.setv(q,'end',[2.45,-1.2])
    assert len(c.child(f,'model'))==1
    c.child(f,'model')[0][1]='${KIPRJMOD}/models/ENVELOPE_TDK_CGA5L1_68N_I32.step'
    changed=[]
    for q in c.child(tree,'segment'):
        ident=c.get(q,'uuid')[0]
        if ident=='a21eb064-90c3-5b4f-82e2-ef1237ccbbe9':
            old=copy.deepcopy(q);a.setv(q,'end',[85.85,-2]);changed.append(dict(before=old,after=q))
        if ident=='cdbc95b1-2d5a-59e1-9f97-3787787ae129':
            old=copy.deepcopy(q);a.setv(q,'start',[85.85,-4.65]);a.setv(q,'end',[85.85,-6.07]);changed.append(dict(before=old,after=q))
    assert len(changed)==2
    additions=[a.parse(f'(segment (start 85.85 -2) (end 85.85 -1.35) (width .15) (layer "B.Cu") (net 142) (uuid "{a.uid("C16668n-CT-tail")}"))')]
    tree.extend(additions);pcb.write_text(a.dump(tree))
    path=a.CAD/'Power_3V3.kicad_sch';sch=c.sx.loads(path.read_text())
    sym=next(s for s in c.child(sch,'symbol')if c.prop(s).get('Reference')=='C166')
    for key,value in props.items():a.prop(sym,key,value)
    for q in c.child(sch,'text'):
        q[1]=q[1].replace('C159/C16633nF C0G control independent charging.','C15933nF / C16668nF C0G control independent charging.')
    path.write_text(a.dump(sch))
    # Preserve the existing tailored footprint identifier, updated exactly.
    b=k.LoadBoard(str(pcb));fp=next(f for f in b.GetFootprints()if f.GetReference()=='C166')
    clone=k.FOOTPRINT(fp);clone.Flip(clone.GetPosition(),False);clone.SetOrientation(k.EDA_ANGLE(0,k.DEGREES_T));clone.SetPosition(k.VECTOR2I(0,0));k.FootprintSave(str(a.CAD/'libraries/RevB.pretty'),clone)
    record=dict(input_PCB_sha256=INPUT_SHA,output_PCB_sha256=hashlib.sha256(pcb.read_bytes()).hexdigest(),part_before=before,part_after=f,changed_copper=changed,added_copper=additions,reason='U121 source-bound4.75V/minimum-current corner collapses while charging maximum C206 at33nF timing and delivering750mA.68nF limits additional reservoir current; tested without reducing load or tuning converter coefficients.',land_mm=dict(PA=2.2,PB=1.1,PC=1.5),body_max_mm=[3.6,1.9,1.9],status='AUTHORED_REQUIRES_NATIVE_AND_AFFECTED_VERIFICATION')
    (a.HERE/'BULK_CHARGE_REFINEMENT.json').write_text(json.dumps(record,indent=2,default=str)+'\n')
    p=a.HERE/'CONTROLLED_RESERVOIR_CHANGES.json';x=json.loads(p.read_text());x['parts']['C166'].update(mpn=MPN,value=VALUE,pcb=[85.85,-3,90,'B.Cu'],fp='RevB:I32_FINISHED_C166',url=props['Datasheet']);x['final_refinement']='BULK_CHARGE_REFINEMENT.json';p.write_text(json.dumps(x,indent=2)+'\n')
    print(record['output_PCB_sha256'])
if __name__=='__main__':main()
