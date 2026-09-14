#!/usr/bin/env python3
"""Reproducible I32 authored changes, starting at the verified I31 CAD checkpoint.

This stages placement and schematic changes. Routing is a separate reviewed
recipe; this intermediate output is deliberately NOT a native passing release.
"""
from pathlib import Path
import copy, hashlib, json, math, subprocess, sys, tempfile, uuid
import pcbnew
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
CAD=HERE.parents[1]/'candidate/cad'
sys.path.insert(0,str(HERE.parent/'convergence_01/support'))
import check_combined_copper as c
sx=c.sx;S=sx.Symbol
BASE='4c3e54395e84483298e453468a65ff2646e9de4e'
def uid(s):return str(uuid.uuid5(uuid.NAMESPACE_URL,'GR86-I32:'+s))
def parse(s):return sx.loads(s)
def dump(t):return '('+str(t[0])+'\n'+'\n'.join(sx.dumps(v)for v in t[1:])+'\n)\n'
def setv(t,k,vals):
 q=c.child(t,k)
 if q:q[0][1:]=vals
 else:t.append([S(k),*vals])
def prop(t,k,v):
 p=next((q for q in c.child(t,'property')if q[1]==k),None)
 if p:p[2]=v
 else:t.append(parse(f'(property {json.dumps(k)} {json.dumps(v)} (at 0 0 0) (effects (font (size 1.0 1.0)) hide))'))
def basefile(p):return subprocess.check_output(['git','show',BASE+':'+str(p.relative_to(ROOT))],cwd=ROOT,text=True)
def label(net,x,y,angle=0):
 return parse(f'(global_label {json.dumps(net)} (shape bidirectional) (at {x} {y} {angle}) (effects (font (size 1 1)) (justify {"left"if angle==0 else"right"})) (uuid "{uid(str((net,x,y,angle)))}") (property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {x} {y} 0) (effects (font (size 1 1)) hide)))')
def wire(a,b,key):return parse(f'(wire (pts (xy {a[0]} {a[1]}) (xy {b[0]} {b[1]})) (stroke (width 0) (type default)) (uuid "{uid(key)}"))')

PARTS={
 'U152':dict(mpn='TPS22953QDQCRQ1',value='TPS22953-Q1 REVERSE BLOCKING',manufacturer='Texas Instruments',lib='RevB:TPS22953QDQCRQ1',fp='RevB:TI_DQC0010A_I32',pcb=[43.6,4.8,0,'B.Cu'],sch=[490.22,63.5],nets={'1':'3V3_ISO_IN','2':'3V3_ISO_IN','3':'3V3_ISO_IN','4':'3V3_ISO_ENABLE','5':'GND','6':'3V3_ISO_CT','7':'3V3_ENABLE','8':'3V3_ISO_SNS','9':'3V3_VIN','10':'3V3_VIN','11':'GND'},url='https://www.ti.com/lit/ds/symlink/tps22953-q1.pdf'),
 'C159':dict(mpn='CGA3E2C0G1H682J080AA',value='6.8n /50V C0G 5% CT',manufacturer='TDK',lib='Device:C',fp='RevB:C_0603_1608Metric',pcb=[46.6,3.0,0,'B.Cu'],sch=[533.4,127],nets={'1':'3V3_ISO_CT','2':'GND'},url='https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=CGA3E2C0G1H682J080AA'),
 'C161':dict(mpn='GCM188R71H104KA57D',value='100n /50V X7R ISO INPUT',manufacturer='Murata',lib='Device:C',fp='RevB:C_0603_1608Metric',pcb=[40.6,4.5,0,'B.Cu'],sch=[533.4,355.6],nets={'1':'3V3_ISO_IN','2':'GND'},url='https://www.murata.com/en-us/products/productdetail?partno=GCM188R71H104KA57D'),
 'R159':dict(mpn='CRCW0603100KFKEA',value='100k /1% PG PULLUP',manufacturer='Vishay',lib='Device:R',fp='RevB:R_0603_1608Metric',pcb=[46,-1.5,0,'F.Cu'],sch=[449.58,177.8],nets={'1':'+5V','2':'3V3_ENABLE'},url='https://www.vishay.com/docs/20035/dcrcwe3.pdf'),
 'R160':dict(mpn='CRCW0603634KFKEA',value='634k /1% SNS TOP',manufacturer='Vishay',lib='Device:R',fp='RevB:R_0603_1608Metric',pcb=[27,-7.5,0,'F.Cu'],sch=[449.58,228.6],nets={'1':'3V3_VIN','2':'3V3_ISO_SNS'},url='https://www.vishay.com/docs/20035/dcrcwe3.pdf'),
 'R161':dict(mpn='CRCW0603100KFKEA',value='100k /1% SNS BOTTOM',manufacturer='Vishay',lib='Device:R',fp='RevB:R_0603_1608Metric',pcb=[30.5,-7.5,0,'F.Cu'],sch=[533.4,228.6],nets={'1':'3V3_ISO_SNS','2':'GND'},url='https://www.vishay.com/docs/20035/dcrcwe3.pdf'),
 'R162':dict(mpn='CRCW0603470KFKEA',value='470k /1% ISO ENABLE TOP',manufacturer='Vishay',lib='Device:R',fp='RevB:R_0603_1608Metric',pcb=[27,-4,0,'F.Cu'],sch=[449.58,127],nets={'1':'+5V','2':'3V3_ISO_ENABLE'},url='https://www.vishay.com/docs/20035/dcrcwe3.pdf'),
 'R163':dict(mpn='CRCW0603100KFKEA',value='100k /1% ISO ENABLE BOTTOM',manufacturer='Vishay',lib='Device:R',fp='RevB:R_0603_1608Metric',pcb=[30.5,-4,0,'F.Cu'],sch=[533.4,177.8],nets={'1':'3V3_ISO_ENABLE','2':'GND'},url='https://www.vishay.com/docs/20035/dcrcwe3.pdf'),
 'TP154':dict(mpn='BARE PCB PAD',value='TP_ISO_ENABLE',manufacturer='PCB',lib='Connector:TestPoint',fp='RevB:TestPoint_Pad_D1.5mm',pcb=[33,-1,0,'F.Cu'],sch=[449.58,279.4],nets={'1':'3V3_ISO_ENABLE'},url=''),
 'C162':dict(mpn='T598X477M010ATE025',value='470u /10V POLYMER INPUT',manufacturer='KEMET',lib='Device:C',fp='RevB:KEMET_T598_X_7343_Median',pcb=[49,-5,0,'F.Cu'],sch=[110.49,386.08],nets={'1':'3V3_VIN','2':'GND'},url='https://content.kemet.com/datasheets/KEM_T2073_T59X.pdf'),
 'C163':dict(mpn='T598X477M010ATE025',value='470u /10V POLYMER INPUT',manufacturer='KEMET',lib='Device:C',fp='RevB:KEMET_T598_X_7343_Median',pcb=[39,-5,0,'F.Cu'],sch=[210.82,386.08],nets={'1':'3V3_VIN','2':'GND'},url='https://content.kemet.com/datasheets/KEM_T2073_T59X.pdf'),
 'C164':dict(mpn='T598X477M010ATE025',value='470u /10V POLYMER INPUT',manufacturer='KEMET',lib='Device:C',fp='RevB:KEMET_T598_X_7343_Median',pcb=[19,-5,0,'F.Cu'],sch=[311.15,386.08],nets={'1':'3V3_VIN','2':'GND'},url='https://content.kemet.com/datasheets/KEM_T2073_T59X.pdf'),
 'C165':dict(mpn='CGA3E3X7R1H224K080AB',value='220n /50V X7R EN DELAY',manufacturer='TDK',lib='Device:C',fp='RevB:C_0603_1608Metric',pcb=[27,-0.5,0,'F.Cu'],sch=[449.58,386.08],nets={'1':'3V3_ENABLE','2':'GND'},url='https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=CGA3E3X7R1H224K080AB'),
 'Q152':dict(mpn='DMG2302UKQ-7',value='DMG2302UKQ /DISCHARGE',manufacturer='Diodes Incorporated',lib='RevB:DMG2302UKQ',fp='RevB:SOT-23',pcb=[46, 44, 0, 'F.Cu'],sch=[490.22, 330.2],nets={'1': '3V3_DISCHARGE_GATE', '2': 'GND', '3': '3V3_DISCHARGE_DRAIN'},url='https://www.diodes.com/assets/Datasheets/DMG2302UKQ.pdf'),
 'Q153':dict(mpn='DMG2302UKQ-7',value='DMG2302UKQ /DISCHARGE',manufacturer='Diodes Incorporated',lib='RevB:DMG2302UKQ',fp='RevB:SOT-23',pcb=[50, 44, 0, 'F.Cu'],sch=[541.02, 330.2],nets={'1': '3V3_ENABLE', '2': 'GND', '3': '3V3_DISCHARGE_GATE'},url='https://www.diodes.com/assets/Datasheets/DMG2302UKQ.pdf'),
 'R164':dict(mpn='CRCW06034K70FKEA',value='4.7k /DISCHARGE GATE FEED',manufacturer='Vishay',lib='Device:R',fp='RevB:R_0603_1608Metric',pcb=[48,48.2,0,'F.Cu'],sch=[508,355.6],nets={'1':'3V3_VIN','2':'3V3_DISCHARGE_GATE'},url='https://www.vishay.com/docs/20035/dcrcwe3.pdf'),
 'R165':dict(mpn='CRCW25124R70FKEGHP',value='4.7R /1.5W PULSE DISCHARGE',manufacturer='Vishay',lib='Device:R',fp='RevB:R_2512_6332Metric',pcb=[39.5,44,0,'F.Cu'],sch=[558.8,355.6],nets={'1':'3V3_SOURCE','2':'3V3_DISCHARGE_DRAIN'},url='https://www.vishay.com/docs/20043/crcwhpe3.pdf'),
 'D105':dict(mpn='SMCJ110AHE3_A/H',value='SMCJ110A /RAW OV CLAMP',manufacturer='Vishay',lib='Device:D_Zener',fp='RevB:D_SMC',pcb=[27,44,180,'F.Cu'],sch=[190.5,269.24],sheet='Input_Protection.kicad_sch',nets={'1':'REV_BLOCKED_12V','2':'GND'},url='https://www.vishay.com/docs/88394/smcj.pdf'),
}
CHANGES={
 'C206':{'MPN':'T598X337M010ATE025','Value':'330u /10V POLYMER','Capacitance_Condition':'Ceff>=147.84uF stacked engineering bound through125C'},
 'R101':{'MPN':'CRCW251212K1FKEG','Value':'12.1k /1W CTRL SURGE FEED','Datasheet':'https://www.vishay.com/docs/20035/dcrcwe3.pdf'},
 'D101':{'MPN':'S5JHE3_A/H','Value':'S5J /600V REVERSE BLOCK','Datasheet':'https://www.vishay.com/docs/88931/s5a.pdf'},
 'R155':{'MPN':'TNPU060311K3HWEA00','Value':'11.3k /0.02% 2ppm FB TOP'},
 'R158':{'MPN':'WSL2512R4700FEA','Value':'470m /1% BULK DAMPING','Footprint':'RevB:R_2512_6332Metric','Datasheet':'https://www.vishay.com/docs/30100/wsl.pdf'},
}

PIN_DEFS=[('1','IN1','power_in',-15.24,12.7,0),('2','IN2','passive',-15.24,10.16,0),('3','BIAS','power_in',-15.24,5.08,0),('4','EN','input',-15.24,0,0),('5','GND','power_in',-15.24,-10.16,0),('6','CT','passive',15.24,-10.16,180),('7','PG','open_collector',15.24,0,180),('8','SNS','input',15.24,5.08,180),('9','OUT1','power_out',15.24,10.16,180),('10','OUT2','passive',15.24,12.7,180),('11','EP','passive',0,-20.32,90)]
def symbol_definition(name):
 short=name.split(':')[-1]
 props=' '.join(f'(property "{k}" "{v}" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))'for k,v in [('Reference','U'),('Value',short),('Footprint','RevB:TI_DQC0010A_I32'),('Datasheet',PARTS['U152']['url'])])
 pins=' '.join(f'(pin {typ} line (at {x} {y} {ang}) (length 2.54) (name "{pn}" (effects (font (size 1 1)))) (number "{n}" (effects (font (size 1 1)))))'for n,pn,typ,x,y,ang in PIN_DEFS)
 return parse(f'(symbol "{name}" (pin_names (offset 0.508)) (in_bom yes) (on_board yes) {props} (symbol "{short}_0_1" (rectangle (start -12.7 17.78) (end 12.7 -17.78) (stroke (width 0.254) (type default)) (fill (type background)))) (symbol "{short}_1_1" {pins}))')

def fet_definition(name):
 lib=parse(Path('/usr/share/kicad/symbols/Transistor_FET.kicad_sym').read_text())
 f=copy.deepcopy(next(q for q in c.child(lib,'symbol')if q[1]=='Q_NMOS_GSD'));f[1]=name
 for q in c.child(f,'symbol'):q[1]=q[1].replace('Q_NMOS_GSD',name.split(':')[-1])
 prop(f,'Value','DMG2302UKQ');prop(f,'Footprint','RevB:SOT-23');prop(f,'Datasheet','https://www.diodes.com/assets/Datasheets/DMG2302UKQ.pdf')
 return f

def instance(template,ref,p,path):
 s=copy.deepcopy(template);old=c.get(s,'at');x,y=p['sch'];setv(s,'at',[x,y,0]);setv(s,'uuid',[uid(ref+'-symbol')]);setv(s,'lib_id',[p['lib']]);setv(s,'in_bom',[S('no'if ref.startswith('TP')else'yes')]);setv(s,'on_board',[S('yes')]);setv(s,'dnp',[S('no')])
 for q in c.child(s,'property'):
  a=c.get(q,'at');setv(q,'at',[round(a[0]-old[0]+x,5),round(a[1]-old[1]+y,5),0])
 for k,v in {'Reference':ref,'Value':p['value'],'Footprint':p['fp'],'MPN':p['mpn'],'Manufacturer':p['manufacturer'],'Datasheet':p['url'],'Assembly':'BARE PCB'if ref.startswith('TP')else'FACTORY','Qualification':'I32 source candidate; native evidence and qualification conditions control'}.items():prop(s,k,v)
 for q in list(c.child(s,'pin')):s.remove(q)
 if ref in ['C162','C163','C164']:
  prop(s,'Polarity','Positive terminal1; negative terminal2');prop(s,'Height','4.3mm maximum');prop(s,'Capacitance_Condition','Ceff>=210.56uF each stacked engineering bound through125C')
 for n in p['nets']:s.append(parse(f'(pin "{n}" (uuid "{uid(ref+"pin"+n)}"))'))
 prop(s,'LCSC','')
 setv(s,'instances',[parse(f'(project "GR86_CCA_RevB" (path "{path}" (reference "{ref}") (unit 1)))')])
 if ref=='U152':
  for k,dy in [('Reference',-23),('Value',-20)]:
   q=next(q for q in c.child(s,'property')if q[1]==k);setv(q,'at',[x,y+dy,0]);setv(q,'effects',[parse('(font (size 1.27 1.27))')])
 return s

def stage():
 assert pcbnew.GetBuildVersion().startswith("9.0.9"), "Author with pinned KiCad9.0.9 bindings"
 # Import the official KiCad DQC-size footprint then bind TI's exact land pattern.
 std=Path('/usr/share/kicad/footprints/Package_SON.pretty/WSON-10-1EP_2x3mm_P0.5mm_EP0.84x2.4mm.kicad_mod')
 f=parse(std.read_text());f[1]='TI_DQC0010A_I32'
 setv(f,'descr',['TI DQC0010A; datasheet drawing 4223098/A 07/2016; 2x3mm WSON, 0.8mm max body'])
 for pad in c.child(f,'pad'):
  if pad[1] and pad[1]!='11':
   at=c.get(pad,'at');setv(pad,'at',[math.copysign(.95,at[0]),at[1]]);setv(pad,'size',[.5,.25]);setv(pad,'roundrect_rratio',[.2])
  elif not pad[1]:setv(pad,'size',[.8,1.0]);setv(pad,'roundrect_rratio',[.0625])
 for q in list(c.child(f,'model')):f.remove(q)
 # Recompute the courtyard from TI's smaller pads and maximum body, with
 # a 0.25 mm assembly allowance (the generic footprint pads were wider).
 for q in list(f):
  if c.tag(q)in ['fp_line','fp_rect']and c.get(q,'layer')==['F.CrtYd']:f.remove(q)
 f.append(parse('(fp_rect (start -1.45 -1.8) (end 1.45 1.8) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd"))'))
 f.append(parse('(model "${KIPRJMOD}/models/ENVELOPE_TI_DQC0010A_I32.step" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))'))
 (CAD/'libraries/RevB.pretty/TI_DQC0010A_I32.kicad_mod').write_text(dump(f))
 lib=basefile(CAD/'libraries/RevB.kicad_sym');(CAD/'libraries/RevB.kicad_sym').write_text(lib.rstrip()[:-1]+'\n'+sx.dumps(symbol_definition('TPS22953QDQCRQ1'))+'\n'+sx.dumps(fet_definition('DMG2302UKQ'))+'\n)\n')
 trees={p.name:parse(basefile(p))for p in CAD.glob('*.kicad_sch')}
 for tree in trees.values():
  for s in c.child(tree,'symbol'):
   ref=c.prop(s).get('Reference')
   for k,v in CHANGES.get(ref,{}).items():prop(s,k,v)
   if ref in CHANGES:
    prop(s,'LCSC','');prop(s,'Qualification','I32 source candidate; source-bound evidence and physical acceptance control')
 power=trees['Power_3V3.kicad_sch'];setv(c.child(power,'title_block')[0],'date',['2026-09-13'])
 c.child(power,'lib_symbols')[0].append(symbol_definition('RevB:TPS22953QDQCRQ1'))
 instances={c.prop(s).get('Reference'):s for s in c.child(power,'symbol')}
 path=c.get(c.child(c.child(c.child(instances['R155'],'instances')[0],'project')[0],'path')[0],'__unused',None)
 project=c.child(c.child(instances['R155'],'instances')[0],'project')[0];path=c.child(project,'path')[0][1]
 for lab in c.child(power,'global_label'):
  xy=c.get(lab,'at')[:2]
  if xy==[111.76,109.22]:lab[1]='3V3_ENABLE'
  if xy in [[40.64,64.77],[365.76,60.96]]:lab[1]='3V3_ISO_IN'
 fet=fet_definition('RevB:DMG2302UKQ');c.child(power,'lib_symbols')[0].append(fet)
 templates={'RevB:DMG2302UKQ':instances['U151'],'Device:R':instances['R155'],'Device:C':instances['C152'],'Connector:TestPoint':instances['TP151'],'RevB:TPS22953QDQCRQ1':instances['U151']}
 for ref,p in PARTS.items():
  target=power;target_path=path
  if p.get('sheet'):
   target=trees[p['sheet']];template=next(q for q in c.child(target,'symbol')if c.prop(q).get('Reference')=='D103')
   target_path=c.child(c.child(c.child(template,'instances')[0],'project')[0],'path')[0][1]
  else:template=templates[p['lib']]
  p['sheet_path']=target_path
  target.append(instance(template,ref,p,target_path));x,y=p['sch']
  defs=PIN_DEFS if ref=='U152'else [('1','','',0,0,0)]if ref.startswith('TP')else [('1','','',0,3.81,0),('2','','',0,-3.81,0)]
  if ref in ['Q152','Q153']:defs=[('1','','',-5.08,0,0),('2','','',2.54,-5.08,90),('3','','',2.54,5.08,270)]
  if ref=='D105':defs=[('1','','',-3.81,0,0),('2','','',3.81,0,180)]
  for n,_,_,dx,dy,ang in defs:
   at=(round(x+dx,5),round(y-dy,5));end=(round(at[0]+(7.62 if dx>0 else -7.62),5),at[1]);target.append(wire(at,end,ref+'wire'+n));target.append(label(p['nets'][n],*end,180 if dx>0 else 0))
 # Replace stale electrical annotations only on this affected sheet.
 for tx in c.child(power,'text'):
  if 'RVB22 POWER CANDIDATE:'in tx[1]:tx[1]='I32: source setpoint 3.264529V (11.3k/4.99k); 400kHz FPWM retained.\nC206 is 330uF/10V; R158 is 470mOhm WSL2512R4700FEA.\nU152 isolates local U151 VIN when the R162/R163 enable divider falls. Q152/Q153/R165 discharge source when EN falls; R1541k remains.\nSee I32 source-bound SPICE, native and layout evidence; physical qualification remains required.'
  if 'CONTROLLED POWER DEBUG'in tx[1]or 'R128 open isolates'in tx[1]:tx[1]='I32 controlled debug: normal assembly has R128 and R151 fitted.\nFor external +5V open R128. R162/R163 automatically enable U152.\nTP154 observes the EN divider; do not drive it. Never parallel active sources.\nFor external main3V3 programming, open R153 first; do not prebias U151 output.\nProbe U151 VIN at C151.1, source at TP151, main at TP203, ISO enable at TP154.\nAfter off verify all separately powered reservoirs <0.2V. See I32 service sequence.'
 power.append(parse(f'(text "I32 ISOLATION: TPS22953 (not TPS22954); no quick output discharge.\nSNS monitors isolated VIN. PG and C165 delay control U151 EN.\nC162/C163/C164 provide 1410uF input storage; C159 sets turn-on slew.\nR151 remains the upstream isolation link." (at 444.5 307.34 0) (effects (font (size 1.05 1.05)) (justify left top)) (uuid "{uid("isolation-note")}"))'))
 for name,tree in trees.items():
  original=basefile(CAD/name)
  if name in ['Power_3V3.kicad_sch','Input_Protection.kicad_sch']:(CAD/name).write_text(dump(tree))
 b=parse(basefile(CAD/'GR86_CCA_RevB.kicad_pcb'));fps={c.prop(f)['Reference']:f for f in c.child(b,'footprint')}
 netmap={q[2]:q[1]for q in c.child(b,'net')}
 for p in PARTS.values():
  for name in p['nets'].values():
   if name not in netmap:
    netmap[name]=max(netmap.values())+1;b.insert(b.index(c.child(b,'footprint')[0]),[S('net'),netmap[name],name])
 def netpad(f,n,name):
  pad=next(p for p in c.child(f,'pad')if p[1]==n);setv(pad,'net',[netmap[name],name])
 for ref,changes in CHANGES.items():
  for k,v in changes.items():
   if k!='Footprint':prop(fps[ref],k,v)
  prop(fps[ref],'LCSC','')
 def footprint(ref,p,old=None):
  fp=pcbnew.FootprintLoad(str(CAD/'libraries/RevB.pretty'),p['fp'].split(':')[1]);assert fp,p['fp']
  fp.SetReference(ref);fp.SetValue(p['value']);fp.SetFPID(pcbnew.LIB_ID('RevB',p['fp'].split(':')[1]));x,y,angle,layer=p['pcb']
  board=pcbnew.BOARD();board.Add(fp)
  if fp.GetLayer() != (pcbnew.B_Cu if layer=='B.Cu' else pcbnew.F_Cu):fp.Flip(pcbnew.VECTOR2I(0,0),False)
  fp.SetOrientationDegrees(angle);fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y)))
  with tempfile.TemporaryDirectory()as td:
   pp=Path(td)/'f.kicad_pcb';pcbnew.SaveBoard(str(pp),board);t=c.child(parse(pp.read_text()),'footprint')[0]
  setv(t,'uuid',[c.get(old,'uuid')[0]if old is not None else uid(ref+'footprint')])
  setv(t,'path',[c.get(old,'path')[0]if old is not None else p.get('sheet_path',path)+'/'+uid(ref+'-symbol')])
  for k,v in {'MPN':p['mpn'],'Manufacturer':p['manufacturer'],'Datasheet':p['url'],'Assembly':'BARE PCB'if ref.startswith('TP')else'FACTORY','Qualification':'I32 source candidate; native evidence and qualification conditions control'}.items():prop(t,k,v)
  for pad in c.child(t,'pad'):
   n=pad[1]
   if not n:continue
   setv(pad,'uuid',[uid(ref+'-pad-'+n)]);netpad(t,n,p['nets'][n])
   if ref=='U152':
    definition=next(q for q in PIN_DEFS if q[0]==n);setv(pad,'pinfunction',[definition[1]]);setv(pad,'pintype',[definition[2]])
  if ref in ['C162','C163','C164']:
   prop(t,'Height','4.3mm maximum');prop(t,'Polarity','Positive terminal1; negative terminal2');prop(t,'Capacitance_Condition','Ceff>=210.56uF each stacked engineering bound through125C')
  if ref.startswith('TP'):setv(t,'attr',[S('exclude_from_pos_files'),S('exclude_from_bom')])
  for q in list(c.child(t,'duplicate_pad_numbers_are_jumpers')):t.remove(q)
  if ref in ['C162','C163','C164']:
   for q in list(c.child(t,'model')):t.remove(q)
   t.extend(copy.deepcopy(c.child(fps['C206'],'model')))
  return t
 for ref,p in PARTS.items():b.append(footprint(ref,p))
 for ref,pos in [('R151',[38.6,1.7,0,'B.Cu']),('R155',[44.55,10.8,90,'B.Cu']),('R156',[41.25,10.8,270,'B.Cu']),('R158',[82,-4,0,'B.Cu'])]:
  old=fps[ref];pr=c.prop(old);mp=dict(mpn=pr['MPN'],value=pr['Value'],manufacturer=pr.get('Manufacturer','Vishay'),url=pr.get('Datasheet',''),fp=CHANGES.get(ref,{}).get('Footprint',old[1]),pcb=pos,nets={pad[1]:c.get(pad,'net')[1]for pad in c.child(old,'pad')})
  if ref=='R151':mp['nets']['2']='3V3_ISO_IN'
  new=footprint(ref,mp,old);b[b.index(old)]=new;fps[ref]=new
 netpad(fps['U151'],'11','3V3_ENABLE')
 removed=[]
 # Remove all obsolete high-impedance FB tracks/vias and the VIN-to-EN tie.
 remove_ids={'99a942b9-65b0-580e-bde6-aa983db1a3a0','bd103345-0362-494f-aef7-fb00ca3734aa','c080f7dc-6d81-41f2-a277-ea4084872eff','187b93f8-9af0-43ef-a25c-3f3a1e4948f9','8a18f5c9-b653-479a-ab2c-ba4cf304f17a','3db5b38e-33d3-453f-bb8b-27dafa92c950','cd01b19d-26c4-42db-8571-ac0f543b8b9f','8cb33166-2699-5311-b448-a141ed5f9309','70849dce-f027-53f5-81fb-448694c6de51'}
 for t in list(b):
  if c.tag(t)in ['segment','via']and(c.get(t,'net')==[netmap['3V3_FB_ADJ']]or c.get(t,'uuid')[0]in remove_ids):removed.append(c.get(t,'uuid')[0]);b.remove(t)
 for t in c.child(b,'segment'):
  if c.get(t,'uuid')==['e01732e7-0e2e-4e1c-aeb9-71a5a9a45922']:setv(t,'start',[38.8,12.675])
 # Preserve the validated long inner-layer branch geometry as the main-rail
 # feed. Damping moves to the capacitor tab; remove only its old local link.
 for t in list(b):
  if c.tag(t)in ['segment','via']and c.get(t,'net')==[netmap['3V3_BULK_DAMPED']]:
   if c.get(t,'uuid')==['c59ff2f7-91dc-5e62-98e1-71fcfcf5f19c']:
    removed.append(c.get(t,'uuid')[0]);b.remove(t)
   else:setv(t,'net',[netmap['+3V3']])
 # Use the same conservative R110 resistor envelope for the larger R158.
 r110=fps['R110'];r158=fps['R158']
 for m in list(c.child(r158,'model')):r158.remove(m)
 r158.append(parse('(model "${KIPRJMOD}/models/ENVELOPE_WSL2512_I32_R158.step" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))'))
 (CAD/'GR86_CCA_RevB.kicad_pcb').write_text(dump(b))
 inventory=json.loads(basefile(CAD/'FITTED_REFERENCES.json'));inventory['fitted_references']=sorted(inventory['fitted_references']+[r for r in PARTS if not r.startswith('TP')]);inventory['I32_added_references']=[r for r in PARTS if not r.startswith('TP')];inventory['I32_expected_count']=len(inventory['fitted_references']);(CAD/'FITTED_REFERENCES.json').write_text(json.dumps(inventory,indent=2)+'\n')
 report=dict(base_commit=BASE,parts=PARTS,property_changes=CHANGES,removed_copper_uuids=removed,status='PLACEMENT_AND_SCHEMATIC_STAGED_ROUTING_REQUIRED')
 (HERE/'AUTHORED_CHANGES.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'new_fitted':len(inventory['fitted_references']),'removed_copper':len(removed)}))
if __name__=='__main__':stage()
