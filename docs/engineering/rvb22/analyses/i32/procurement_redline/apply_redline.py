#!/usr/bin/env python3
"""Apply the frozen I32 procurement redline once to the verified native source.

The precondition protects subsequent hand edits. Native ERC/DRC, model export,
source parity and procurement qualification remain independent acceptance gates.
"""
from pathlib import Path
import copy, hashlib, json, math, re, sys, uuid

D = Path(__file__).resolve().parent
W = D.parents[2]
CAD = W / 'candidate/cad'
sys.path.insert(0, str(W / 'analyses/convergence_01/support'))
import sexpdata as sx
S = sx.Symbol
BASE_PCB_SHA = '45a2a679d9893d51fa641e539af45bc6ec1324169ea5f2226ecdea0ae2464da7'

def tag(x): return str(x[0]) if isinstance(x,list) and x else ''
def children(x,k): return [a for a in x[1:] if tag(a)==k]
def get(x,k,default=None): return next((a[1:] for a in children(x,k)),default)
def props(x): return {a[1]:a[2] for a in children(x,'property')}
def setv(x,k,v):
    rows=children(x,k)
    if rows: rows[0][1:]=v
    else: x.append([S(k),*v])
def prop(x,k,v):
    row=next((r for r in children(x,'property') if r[1]==k),None)
    if row is None:
        row=copy.deepcopy(next(r for r in children(x,'property') if r[1]=='MPN'))
        row[1]=k
        for q in list(children(row,'uuid')): row.remove(q)
        x.append(row)
    row[2]=v
def dump(x): return '('+str(x[0])+'\n'+'\n'.join(sx.dumps(q) for q in x[1:])+'\n)\n'
def uid(s): return str(uuid.uuid5(uuid.NAMESPACE_URL,'GR86-I32-procurement:'+s))
def spans(text):
    depth=0;quoted=False;escaped=False;start=None
    for i,ch in enumerate(text):
        if quoted:
            if escaped:escaped=False
            elif ch=='\\':escaped=True
            elif ch=='"':quoted=False
        elif ch=='"':quoted=True
        elif ch=='(':
            if depth==1:start=i
            depth+=1
        elif ch==')':
            depth-=1
            if depth==1 and start is not None:yield start,i+1
    assert depth==0 and not quoted

def spec(mpn,lcsc,value,manufacturer,datasheet,**kw):
    return dict(MPN=mpn,LCSC=lcsc,Value=value,Manufacturer=manufacturer,Datasheet=datasheet,**kw)
PTFR='https://jlcpcb.com/partdetail/C19679768'
SPEC={
 'L121':spec('BPCI00121280470M00','C6471075','47u /100mOhm 2.5A BPCI','Chilisin / Pulse','https://jlcpcb.com/partdetail/ChilisinElec-BPCI00121280470M00/C6471075'),
 'R155':spec('PTFR0603B11K8N9','C19679768','11.8k /0.1% 10ppm FB TOP','Resistor.Today',PTFR),
 'R156':spec('PLT1206Z5051LBTS','C4074185','5.05k /0.01% 5ppm FB BOTTOM','Vishay','https://www.vishay.com/docs/60030/plt.pdf'),
 'R160':spec('RT0805BRB076K34L','C864499','6.34k /0.1% 10ppm SNS TOP','YAGEO','https://jlcpcb.com/partdetail/C864499'),
 'R161':spec('PTFR0603Q1K00N9','C23067434','1k /0.02% 10ppm SNS BOTTOM','Resistor.Today',PTFR),
 'R162':spec('PTFR0603Q4K70N9','C23067437','4.7k /0.02% 10ppm ISO EN TOP','Resistor.Today',PTFR),
 'R163':spec('PTFR0603Q1K00N9','C23067434','1k /0.02% 10ppm ISO EN BOTTOM','Resistor.Today',PTFR),
 'R169':spec('PTFR0603B3K01N9','C2692830','3.01k /0.1% 10ppm BULK EN TOP','Resistor.Today',PTFR),
 'R170':spec('PTFR0603Q1K00N9','C23067434','1k /0.02% 10ppm BULK EN BOTTOM','Resistor.Today',PTFR),
 'U101':spec('LTC4367HMS8#PBF','C688370','LTC4367HMS8#PBF','Analog Devices','https://www.analog.com/media/en/technical-documentation/data-sheets/ltc4367.pdf',Qualification='Owner accepts H-grade #PBF without #W controlled-manufacturing pedigree; electrical equivalence only'),
}
for ref in ('C152','C154','C165'):
    SPEC[ref]=spec('CGA3E3X7R1H224KT0Y0N','C342967','220n /50V X7R 10%'+(' EN DELAY' if ref=='C165' else ''),'TDK','https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=CGA3E3X7R1H224KT0Y0N')

# Actual body dimensions (maximum); these generic STEP solids are explicitly
# envelopes, not manufacturer CAD. Placement allowances live in mechanical_check.
MODEL_BOUNDS={'L121':[12.5,12.5,8.0],'R156':[3.4032,1.7272,.8382],'R160':[2.1,1.35,.6]}
for ref in SPEC:
    if SPEC[ref]['MPN'].startswith('PTFR'):MODEL_BOUNDS[ref]=[1.8,1.0,.5]

def box_step(name,xyz,path):
    """Write a standard faceted BREP cuboid in mm, with outward face loops."""
    x,y,z=xyz;x/=2;y/=2
    points=[(-x,-y,0),(x,-y,0),(x,y,0),(-x,y,0),(-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)]
    rows=[]
    def add(s): rows.append(s);return len(rows)
    application=add("APPLICATION_CONTEXT('automotive_design')")
    product_context=add(f"PRODUCT_CONTEXT('',#{application},'mechanical')")
    product=add(f"PRODUCT('{name}','{name}','Generic maximum body envelope; not vendor CAD',(#{product_context}))")
    formation=add(f"PRODUCT_DEFINITION_FORMATION_WITH_SPECIFIED_SOURCE('','',#{product},.NOT_KNOWN.)")
    context=add(f"PRODUCT_DEFINITION_CONTEXT('part definition',#{application},'design')")
    definition=add(f"PRODUCT_DEFINITION('design','',#{formation},#{context})")
    pshape=add(f"PRODUCT_DEFINITION_SHAPE('','',#{definition})")
    ids=[add("CARTESIAN_POINT('',(%s))" % ','.join(f'{v:.8f}' for v in p)) for p in points]
    faces=[]
    for face in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:
        loop=add("POLY_LOOP('',(%s))" % ','.join('#'+str(ids[k]) for k in face))
        bound=add(f"FACE_OUTER_BOUND('',#{loop},.T.)")
        faces.append(add(f"FACE('',(#{bound}))"))
    shell=add("CLOSED_SHELL('',(%s))" % ','.join('#'+str(k) for k in faces))
    brep=add(f"FACETED_BREP('{name}',#{shell})")
    mm=add('(LENGTH_UNIT()NAMED_UNIT(*)SI_UNIT(.MILLI.,.METRE.))')
    rad=add('(NAMED_UNIT(*)PLANE_ANGLE_UNIT()SI_UNIT($,.RADIAN.))')
    ster=add('(NAMED_UNIT(*)SI_UNIT($,.STERADIAN.)SOLID_ANGLE_UNIT())')
    uncertainty=add(f"UNCERTAINTY_MEASURE_WITH_UNIT(LENGTH_MEASURE(1.E-7),#{mm},'distance_accuracy_value','')")
    geom=add(f"(GEOMETRIC_REPRESENTATION_CONTEXT(3)GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT((#{uncertainty}))GLOBAL_UNIT_ASSIGNED_CONTEXT((#{mm},#{rad},#{ster}))REPRESENTATION_CONTEXT('',''))")
    rep=add(f"FACETED_BREP_SHAPE_REPRESENTATION('{name}',(#{brep}),#{geom})")
    add(f'SHAPE_DEFINITION_REPRESENTATION(#{pshape},#{rep})')
    path.write_text("ISO-10303-21;\nHEADER;\nFILE_DESCRIPTION(('Generic maximum body envelope'),'2;1');\nFILE_NAME('"+name+"','2026-09-14T00:00:00',('tranquilWorks'),('tranquilWorks'),'I32 procurement box generator','I32','');\nFILE_SCHEMA(('AUTOMOTIVE_DESIGN'));\nENDSEC;\nDATA;\n"+'\n'.join(f'#{i} = {s};' for i,s in enumerate(rows,1))+'\nENDSEC;\nEND-ISO-10303-21;\n')

def rect(f,layer,half):
    x,y=half
    f.append(sx.loads(f'(fp_rect (start {-x} {-y}) (end {x} {y}) (stroke (width 0.05) (type default)) (fill no) (layer "{layer}") (uuid "{uid(str(f[1])+layer)}"))'))

def shape(f,ref):
    side=get(f,'layer')[0][0];angle=(get(f,'at')+[0])[2]
    if ref not in MODEL_BOUNDS:return
    if ref=='L121':
        pad_size=[5.4,2.8];locations=[[0,-4.9],[0,4.9]];body=[6,6];court=[6.55,6.55]
    elif ref=='R156':
        # Vishay 60119 p1: 0.156 overall, 0.084 gap, 0.036 pad, 0.067 width.
        pad_size=[.9144,1.7018];locations=[[-1.524,0],[1.524,0]];body=[1.6002,.8001];court=[2.25,1.125]
        # Keep the existing ground pad connection to within 1 um, clearing C152.
        setv(f,'at',[41.25,10.101,-90])
    elif ref=='R160':
        # IPC nominal 0805 lands, verified against YAGEO RT V16 Table 1.
        pad_size=[1.0,1.45];locations=[[-1.025,0],[1.025,0]];body=[1,.625];court=[1.775,.975]
    else:
        # Resistor.Today PTFR p3 a=3.0+/-0.2,b=1.2+/-0.2,c=1.0+/-0.2.
        # Use a=2.8,b=1.2,c=1.0, within the manufacturer's drawing limits.
        pad_size=[.9,1.2];locations=[[-.95,0],[.95,0]];body=[.8,.4];court=[1.65,.9]
    for p,at in zip(sorted(children(f,'pad'),key=lambda p:p[1]),locations):
        setv(p,'at',at+([angle%360] if angle else []));setv(p,'size',pad_size)
        p[3]=S('rect')
        for q in list(children(p,'roundrect_rratio')):p.remove(q)
    # Tailored original silkscreen references stay in place. New Fab/courtyard
    # outlines describe the actual package; no footprint mismatch is waived.
    for q in list(f):
        if tag(q).startswith('fp_') and get(q,'layer',[''])[0].endswith(('Fab','CrtYd')):f.remove(q)
    rect(f,side+'.Fab',body);rect(f,side+'.CrtYd',court)
    model='ENVELOPE_I32_PROCUREMENT_'+ref+'.step'
    for q in list(children(f,'model')):f.remove(q)
    f.append(sx.loads(f'(model "${{KIPRJMOD}}/models/{model}" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))'))
    box_step('I32_'+ref+'_MAXIMUM_BODY',MODEL_BOUNDS[ref],CAD/'models'/model)

def main():
    pcb=CAD/'GR86_CCA_RevB.kicad_pcb';text=pcb.read_text()
    assert hashlib.sha256(pcb.read_bytes()).hexdigest()==BASE_PCB_SHA,'Source changed: do not rerun this one-shot authoring recipe'
    before={};replacements=[];fps={}
    for lo,hi in spans(text):
        if not text[lo:hi].startswith('(footprint '):continue
        f=sx.loads(text[lo:hi]);ref=props(f)['Reference']
        if ref not in SPEC:continue
        before[ref]=dict(footprint=f[1],properties=props(f),at=get(f,'at'),pads=children(f,'pad'))
        f[1]='RevB:I32_PROCUREMENT_'+ref
        for k,v in SPEC[ref].items():prop(f,k,v)
        shape(f,ref)
        fps[ref]=f
        replacements.append((lo,hi,dump(f).strip()))
    assert set(fps)==set(SPEC)
    for lo,hi,s in reversed(replacements):text=text[:lo]+s+text[hi:]
    # FB copper was already routed to the former pad centre. Extend this same
    # net on B.Cu to the new pin 1; the original ground pad centre is retained.
    fb=sx.loads(f'(segment (start 41.25 9.975) (end 41.25 8.577) (width 0.25) (layer "B.Cu") (net 131) (uuid "{uid("R156-feedback-extension")}"))')
    text=text.rstrip();text=text[:-1]+sx.dumps(fb)+'\n)\n';pcb.write_text(text)
    sheets={}
    for path in CAD.glob('*.kicad_sch'):
        text=path.read_text();rr=[]
        for lo,hi in spans(text):
            if not text[lo:hi].startswith('(symbol '):continue
            sym=sx.loads(text[lo:hi]);ref=props(sym).get('Reference')
            if ref not in SPEC:continue
            for k,v in SPEC[ref].items():prop(sym,k,v)
            prop(sym,'Footprint','RevB:I32_PROCUREMENT_'+ref)
            if ref=='U101':setv(sym,'lib_id',['RevB:LTC4367HMS8_PBF'])
            rr.append((lo,hi,sx.dumps(sym)));sheets[ref]=path.name
        for lo,hi,s in reversed(rr):text=text[:lo]+s+text[hi:]
        if rr:
            # Same H-grade symbol/pin geometry; explicit non-W ordering alias.
            if 'U101' in [r for r,p in sheets.items() if p==path.name]:text=text.replace('LTC4367HMS8_WTRPBF','LTC4367HMS8_PBF')
            path.write_text(text)
    assert set(sheets)==set(SPEC)
    lib=CAD/'libraries/RevB.kicad_sym';text=lib.read_text()
    # Preserve the old symbol as a historical reusable library entry, add exact
    # PBF alias with identical pins. Only the new alias is active in the design.
    old=next(text[lo:hi] for lo,hi in spans(text) if text[lo:hi].startswith('(symbol "LTC4367HMS8_WTRPBF"'))
    new=old.replace('LTC4367HMS8_WTRPBF','LTC4367HMS8_PBF')
    text=text.rstrip();lib.write_text(text[:-1]+new+'\n)\n')
    (D/'AUTHORED_REDLINE.json').write_text(json.dumps(dict(baseline_PCB_sha256=BASE_PCB_SHA,before=before,specifications=SPEC,sheets=sheets,maximum_body_envelopes_mm=MODEL_BOUNDS,model_type='Dimensionally bounded generic STEP, not vendor geometry',new_feedback_segment=fb,physical_tests_performed=0),indent=2,default=str)+'\n')
    print('Applied',len(SPEC),'frozen references. Native library synchronization and all verification still required.')

if __name__=='__main__':main()
