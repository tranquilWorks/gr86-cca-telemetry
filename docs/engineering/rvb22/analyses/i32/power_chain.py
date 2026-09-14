#!/usr/bin/env python3
"""I32 physical network and sequencer; original bounded behavioral models.

U151 coefficients are inherited, with explicit sensitivities, never fitted to
make the selected network pass. TPS22953 includes SNS-falling automatic restart.
The documented typical delays lack max limits; tested allocations are conditions
for physical acceptance, not guaranteed silicon timing.
"""
from pathlib import Path
import argparse,concurrent.futures as cf,hashlib,json,subprocess,gzip,shutil,tempfile
import numpy as np
D=Path(__file__).resolve().parent
BASE=(D.parent/'i31/nominal_cascade.cir').read_text()
MODEL=(D.parent/'i31/lm63615_derivative.lib').read_text()
def inherited_network(p):
 s=BASE.replace('I31 U151 derivative startup; not TI encrypted model','I32 exploratory network alternative; not manufacturer U151 model')
 s=s.replace('C206 damped C206_ESR 0.00047',f"C206 damped C206_ESR {p['bulk_uF']*1e-6}")
 s=s.replace('R158 main damped 0.082',f"R158 main damped {p['damp']}")
 s=s.replace('R155 source fb 11800',f"R155 source fb {p['top']}")
 s=s.replace('TSS=0.0016',f"TSS={p.get('tss',.0016)}")
 if p.get('slow'):
  s=s.replace('KP=14.4 FZ=1000 FP=80000 TI=3e-06','KP=7.2 FZ=500 FP=40000 TI=6e-06')
 if p.get('isolate'):
  s=s.replace('R151 rail5 vin .005','''* LM66100-Q1 isolation hypothesis. Datasheet bounds, not vendor model.
R151 rail5 iso_in .005
Bdif isod 0 V={v(iso_in,vin)}
Risodelay isod isodelayed 1k
Cisodelay isodelayed 0 2n
Siso iso_in vin isodelayed 0 iso_sw
.model iso_sw SW(Ron=.14 Roff=1e12 Vt=.085 Vh=.165)
Diso iso_in vin diso_body
.model diso_body D(Is=1p N=1.5 Rs=.1)
Biso_leak vin iso_in I={8u*clip(v(vin,iso_in),0,1)}''')
  s=s.replace('C_OTHER5 vin 0','C_OTHER5 rail5 0').replace('Bother5 vin 0','Bother5 rail5 0').replace('clip(v(vin)/4.5','clip(v(rail5)/4.5')
  s=s.replace('Suv one enable vin 0 uv_sw','Suv one enable source5 0 uv_sw').replace('Vt=3.25 Vh=0.25','Vt=4.57 Vh=0.15')
 if p.get('mode')=='off':
  s=s.replace('PWL(0 0 1m 0 2m 12)','PWL(0 0 1m 0 2m 12 80m 12 80.1m 0 200m 0 200.1m 12)')
  s=s.replace('0.12 0 2e-06','0.3 0 2e-06')
 if p.get('mode')=='load':
  s=s.replace('Vload requested 0 DC .45','Vload requested 0 PWL(0 .45 75m .45 75.001m .75 85m .75 85.001m .02 95m .02 95.001m .45)')
 if p.get('constant'):
  s=s.replace('v(requested)*(v(ready)>.5 ? 1 : .020/.45)',str(p['constant']))
 return s
def isolation_network(p):
 s=inherited_network(dict(bulk_uF=p['bulk'],damp=p['damp'],top=p.get('top',11500),isolate=False,mode=p.get('mode'),slow=p.get('slow'),constant=p.get('constant'),tss=p.get('tss',.0016)))
 s=s.replace('R154 main 0 1k',f"R154 main 0 {p.get('bleed',330)}")
 s=s.replace('C_OTHER5 vin 0','C_OTHER5 rail5 0').replace('Bother5 vin 0','Bother5 rail5 0').replace('clip(v(vin)/4.5','clip(v(rail5)/4.5')
 s=s.replace('R151 rail5 vin .005',f'''* Controlled reverse-blocking load switch, NOT its vendor transistor model.
* 5V PGOOD: min/max crossings swept separately. 100us fall lag is allocation.
R151 rail5 feediso .005
Sgood5 one good5 source5 0 good5model
Rgood5 good5 0 1k
.model good5model SW(Ron=.01 Roff=1e12 Vt={p.get('pg_mid',4.51)} Vh={p.get('pg_hys',.1)})
Rgooddelay good5 gooddelay 1
Cgooddelay gooddelay 0 {p.get('off_delay',100e-6)/.693147}
Bage 0 ageiso I={{v(gooddelay)>.5 ? 1 : -v(ageiso)/1u}}
Cageiso ageiso 0 1 IC=0
Rageiso ageiso 0 1e12
Bvslew slewiso 0 V={{min(max((v(ageiso)-{p.get('tdelay',.0005)})/{p.get('slew',370e-6)},0),max(v(feediso),0))}}
* Conductance servo only models slew-limited turn-on. It has no artificial current limit.
Vpass feediso feedpass 0
Bpass feedpass vin I={{v(gooddelay)>.5 ? v(feediso,vin)*min(1/{p.get('ron',.04)},max(v(slewiso,vin),0)*1e6) : -{p.get('leak',100e-6)}*clip(v(vin),0,1)}}
Bbias feediso 0 I={{50u*clip(v(feediso),0,1)}}
C160 vin 0 {22e-6*p.get('cin_scale',1)}
R160 vin snsiso 681k
R161 snsiso 0 100k
Bic151 vin 0 I={{10u*clip(v(vin),0,1)}}
* Reserve additional leakage for both MLCC banks and board, independent of switch allocation.
Bcapleak vin 0 I={{5u*clip(v(vin),0,1)}}
Sgoodlocal one localgood snsiso 0 snsmodel
Rgoodlocal localgood 0 1k
.model snsmodel SW(Ron=.01 Roff=1e12 Vt={p.get('sns_mid',.485)} Vh={p.get('sns_hys',.03)})
Rpgdelay localgood pgdelay 1
Cpgdelay pgdelay 0 145u
Benable enable_ctrl 0 V={{v(gooddelay)>.5 && v(pgdelay)>.5 ? 1 : 0}}''')
 s=s.replace('Suv one enable vin 0 uv_sw','Suv one enable enable_ctrl 0 uv_sw').replace('Vt=3.25 Vh=0.25','Vt=.5 Vh=.01')
 if p.get('highref'):s=s.replace('VREF=1.0 TSS','VREF=1.0156 TSS')
 for line in s.splitlines():
  if line.startswith(('C155 ','C156 ','C157 ','C201 ','C204 ')):
   words=line.split();words[-1]=str(float(words[-1])*p.get('ceramic',1));s=s.replace(line,' '.join(words))
 s=s.replace(f"C206 damped C206_ESR {p['bulk']*1e-6}",f"C206 damped C206_ESR {p['bulk']*1e-6*p.get('bulk_scale',1)}")
 s=s.replace('R_C206 C206_ESR 0 0.025',f"R_C206 C206_ESR 0 {p.get('esr',.025)}")
 if p.get('mode')=='off':
  s=s.replace('200m 0 200.1m 12','750m 0 750.1m 12').replace('0.3 0 2e-06','0.85 0 2e-06')
 s=s.replace('C151 vin C151_esr 2.2e-05',f"C151 vin C151_esr {22e-6*p.get('cin_scale',1)}")
 if p.get('no_off_load'):s=s.replace('(v(ready)>.5 ? 1 : .020/.45)','(v(ready)>.5 ? 1 : 0)')
 s=s.replace('v(PROTECTED_12V)\n','v(PROTECTED_12V) v(good5) v(gooddelay) v(snsiso) v(pgdelay) i(Vpass)\n')
 return s

def build(p):
 s=isolation_network(p)
 if not p.get('constant'):
  # Pre-reset module load is independent of the later requested run current.
  s=s.replace('v(requested)*(v(ready)>.5 ? 1 : .020/.45)',f"(v(ready)>.5 ? v(requested) : {p.get('pre_reset_load',.020)})")
 if p.get('reset_delay'):
  s=s.replace('Ctimer timer 0 2e-08 IC=0',f"Ctimer timer 0 {p['reset_delay']*1e-6} IC=0")
 if p.get('main_feed_R'):
  s=s.replace('R153 source main 0.01',f"R153 source main_feed 0.01\nRmainfeed main_feed main_l {p['main_feed_R']}\nLmainfeed main_l main {p.get('main_feed_L',300e-9)}")
 if p.get('reset_fall'):
  fall=p['reset_fall'];rise=fall+p.get('reset_hys',.07675)
  s=s.replace('Vt=3.08535 Vh=0.01535',f'Vt={(rise+fall)/2} Vh={(rise-fall)/2}')
 for ref in ['C201','C204']:
  line=next(x for x in s.splitlines()if x.startswith(ref+' '));w=line.split();w[-1]=str(float(w[-1])*p.get('main_ceramic_multiplier',1));s=s.replace(line,' '.join(w))
 if p.get('cff'):s=s.replace('.control',f"C166ff source fb {p['cff']}\n.control")
 s=s.replace('TDELAY=0.001',f"TDELAY={p.get('tdelay151',.001)}")
 s=s.replace('L121 sw5 winding5 4.7e-05',f"L121 sw5 winding5 {47e-6*p.get('L121_scale',1)}")
 s=s.replace('L151 sw winding 1.5e-05',f"L151 sw winding {15e-6*p.get('L151_scale',1)}")
 s=s.replace('R_L151 winding source 0.0771',f"R_L151 winding source {0.0771*p.get('inductor_DCR_scale',1)}")
 s=s.replace('R_L121 winding5 source5 0.187',f"R_L121 winding5 source5 {0.187*p.get('inductor_DCR_scale',1)}")
 s=s.replace('LNOM=47u IPOS=1.05',f"LNOM=47u IPOS={p.get('ipos121',1.05)}")
 # Current source R101 and diode voltage rating affect the upstream chain.
 s=s.replace('PROTECT_CTRL_VIN 6.81k','PROTECT_CTRL_VIN 12.1k')
 s=s.replace('Vt=4.51 Vh=0.1',f"Vt={(p.get('pg_rise',4.6626)+p.get('pg_fall',4.4172))/2} Vh={(p.get('pg_rise',4.6626)-p.get('pg_fall',4.4172))/2}")
 # SNS input hysteresis and resistor/leakage extrema are modeled as thresholds
 # at the divider pin; edge detector cannot repeatedly trip on held-low SNS.
 s=s.replace('Vt=0.485 Vh=0.03',f"Vt={(p.get('sns_rise',.515)+p.get('sns_fall',.455))/2} Vh={(p.get('sns_rise',.515)-p.get('sns_fall',.455))/2}")
 s=s.replace('R160 vin snsiso 681k',f"R160 vin snsiso {p.get('sns_top',681000)*p.get('sns_top_scale',1)}")
 s=s.replace('R161 snsiso 0 100k',f"R161 snsiso 0 {p.get('sns_bottom',100000)*p.get('sns_bottom_scale',1)}")
 s=s.replace(f"Rgooddelay good5 gooddelay 1\nCgooddelay gooddelay 0 {p.get('off_delay',100e-6)/.693147}",f"Bgooddelay 0 gooddelay I={{(v(good5)-v(gooddelay))/(v(good5)>v(gooddelay) ? {p.get('source_pg_blank',100e-6)/.693147} : {p.get('off_delay',100e-6)/.693147})}}\nCgooddelay gooddelay 0 1 IC=0")
 s=s.replace('Bage 0 ageiso I={v(gooddelay)>.5','Bage 0 ageiso I={v(switchon)>.5')
 s=s.replace('v(gooddelay)>.5 ? v(feediso,vin)','v(switchon)>.5 ? v(feediso,vin)')
 # Convert SNS to deglitched state, detect only its falling edge, and hold
 # the switch off for restart time even if SNS recovers before that time.
 extra=f"""
Bsnsfilter 0 snsfiltered I={{(v(localgood)-v(snsfiltered))/{p.get('sns_deglitch',5e-6)/.693147}}}
Csnsfilter snsfiltered 0 1 IC=0
Bsnsprev 0 snsprev I={{(v(snsfiltered)-v(snsprev))/1u}}
Csnsprev snsprev 0 1 IC=0
Bsnsevent snsevent 0 V={{clip((v(snsprev)-v(snsfiltered)-.02)/.01,0,1)*clip((.5-v(snsfiltered))/.01,0,1)}}
Brestart 0 restartage I={{-v(snsevent)*v(restartage)/10n + (1-v(snsevent))*clip((.1-v(restartage))/.001,0,1)}}
Crestart restartage 0 1 IC=0
Rrestart restartage 0 1e12
Bswitchon switchon 0 V={{v(gooddelay)>.5 && v(restartage)>{p.get('restart',.002)} ? 1 : 0}}
"""
 s=s.replace('Rpgdelay localgood pgdelay 1\nCpgdelay pgdelay 0 145u',extra+f"Bpgwant pgwant 0 V={{min(v(localgood),v(switchon))}}\nBpgdelay 0 pgdelay I={{(v(pgwant)-v(pgdelay))/(v(pgwant)>v(pgdelay) ? {p.get('pg_blank',100e-6)/.693147} : {p.get('pg_fall_delay',5e-6)/.693147})}}\nCpgdelay pgdelay 0 1 IC=0")
 # New isolated input capacitor has finite ESR; the branch trace has R/L.
 s=s.replace(f"C160 vin 0 {22e-6*p.get('cin_scale',1)}",f"R_C160 vin c160esr {p.get('c160_esr',.012)}\nC160 c160esr 0 {p.get('c160',22e-6)*p.get('c160_scale',1)}")
 s=s.replace(f"R158 main damped {p['damp']}",f"VR158 main branch_sense 0\nRbranch branch_sense branch_l {p.get('branch_R',.06)}\nLbranch branch_l branch_r {p.get('branch_L',50e-9)}\nR158 branch_r damped {p['damp']}")
 if p.get('en_cap'):
  s=s.replace('Benable enable_ctrl 0 V={v(gooddelay)>.5 && v(pgdelay)>.5 ? 1 : 0}',f'''Bpgsink en151 0 I={{(1-clip(v(pgdelay),0,1))*v(en151)/400}}
R159pull rail5 en151 100k
C165en en151 0 {p['en_cap']}
Benleak en151 0 I={{300n*clip(v(en151),0,1)}}
S151en one enable_ctrl en151 0 en151model
R151en enable_ctrl 0 1k
.model en151model SW(Ron=.01 Roff=1e12 Vt={(p.get('en_rise',1.5)+p.get('en_fall',.94))/2} Vh={(p.get('en_rise',1.5)-p.get('en_fall',.94))/2})''')
 s=s.replace('IPOS=1.7 INEG=0.75',f"IPOS={p.get('ipos',1.7)} INEG={p.get('ineg',.75)}")
 s=s.replace('VREF=1.0 TSS',f"VREF={p.get('vref',1.0)} TSS").replace('VREF=1.0156 TSS',f"VREF={p.get('vref',1.0156)} TSS")
 s=s.replace('Bcapleak vin 0 I={5u*clip(v(vin),0,1)}',f"Bcapleak vin 0 I={{{p.get('input_leak',5e-6)}*clip(v(vin),0,1)}}")
 s=s.replace('R155 source fb 11300',f"R155 source fb {11300*p.get('fb_top_scale',1)}").replace('R156 fb 0 4990',f"R156 fb 0 {4990*p.get('fb_bottom_scale',1)}")
 if p.get('fb_target'):
  line=next(x for x in s.splitlines()if x.startswith('R155 '))
  s=s.replace(line,f"R155 source fb {p['fb_target']*p.get('fb_top_scale',1)}")
 if p.get('fb_bottom_target'):
  line=next(x for x in s.splitlines()if x.startswith('R156 '))
  s=s.replace(line,f"R156 fb 0 {p['fb_bottom_target']*p.get('fb_bottom_scale',1)}")
 if p.get('remote_sense'):
  # Explicit load ground preserves its voltage shift relative to U151 AGND.
  # The sense lead sees the physical positive rail; supervisor and load see
  # mainpos minus load-ground. Rfeed+Rreturn retains the extracted loop bound.
  lines=[]
  for line in s.splitlines():
   w=line.split()
   if w and w[0]in ['R155']:
    w[1]='mainpos';line=' '.join(w)
   elif w and (w[0].startswith(('C201','C204','C202','C205','C301','C302','C404','C531'))or w[0]in ['VR158','R154','Bload']):
    line=line.replace(' main ',' mainpos ',1)
    if w[0]in ['R154','Bload']:line=line.replace(' mainpos 0 ',' mainpos loadground ',1)
   elif w and w[0]in ['R_C201','R_C204','R_C202','R_C205','R_C301','R_C302','R_C404','R_C531','R_C206']:
    w[2]='loadground';line=' '.join(w)
   elif w and w[0]=='Lmainfeed':line=line.replace(' main ',' mainpos ')
   elif w and w[0]=='Rmainfeed':w[-1]=str(p['main_feed_R']-p.get('return_R',.015));line=' '.join(w)
   lines.append(line)
  s='\n'.join(lines)+'\n'
  s=s.replace('.control',f"Rloadground loadground 0 {p.get('return_R',.015)}\nBmainmeas main 0 V={{v(mainpos,loadground)}}\n.control")
 if p.get('battery_pwl'):s=s.replace('VBAT BAT 0 PWL(0 0 1m 0 2m 12)','VBAT BAT 0 PWL('+p['battery_pwl']+')')
 if p.get('stop'):s=s.replace('0.12 0 2e-06',str(p['stop'])+' 0 2e-06')
 if p.get('sns_fault'):
  s=s.replace('R161 snsiso 0 ', 'R161 snsiso snsbase ')
  t=p.get('fault_start',.15)
  s=s.replace('.control',f'Vsnsbase snsbase 0 PWL(0 0 {t} 0 {t+1e-6} -4 {t+.000201} -4 {t+.000202} 0)\n.control')
 if p.get('active_discharge'):
  discharge=f'''R164gate vin disg {p.get('r164',4700)}
Cdisg disg 0 {p.get('q_gate_c',2e-9)}
Bq152gate disg 0 I={{{p.get('q_gate_leak',20e-6)}*clip(v(disg),0,1)}}
Bq153gate en151 0 I={{{p.get('q_gate_leak',20e-6)}*clip(v(en151),0,1)}}
Bq153 disg 0 I={{v(disg)*clip((v(en151)-{p.get('q153_threshold',1.0)})/.1,0,1)/{p.get('q_ron',.3)}}}
R165 source disdrain {p.get('r165',22)}
Bq152 disdrain 0 I={{v(disdrain)*clip((v(disg)-{p.get('q152_threshold',2.5)})/.1,0,1)/{p.get('q_ron',.3)}}}
Dq152body 0 disdrain body_diode
'''
  s=s.replace('.control',discharge+'\n.control')
 if p.get('enable_divider'):
  # PG and Q153 gate rise before U151's divided EN. Shutdown ordering also
  # depends on Q153's low-current transfer curve and is swept separately.
  s=s.replace('R159pull rail5 en151 100k',f"R159pull rail5 en151 {p.get('pg_pullup',47000)}")
  s=s.replace('Benleak en151 0','Benleak actual_en151 0')
  s=s.replace('S151en one enable_ctrl en151 0','S151en one enable_ctrl actual_en151 0')
  s=s.replace('.control',f"R166en en151 actual_en151 {330000*p.get('en_top_scale',1)}\nR167en actual_en151 0 {330000*p.get('en_bottom_scale',1)}\nCen151 actual_en151 0 {p.get('actual_en_cap',10e-12)}\n.control")
 if p.get('external5'):
  # R128 open; R162/R163 remain fitted and automatically enable U152.
  s=s.replace('R128 source5 rail5 .005','R128 source5 rail5 1e12\nVservice rail5 0 PWL(0 0 1m 0 2m 5)')
  s=s.replace('source5 0 good5model','rail5 0 good5model')
  s=s.replace('i(VBAT)','i(Vservice)')
 if p.get('physical_dividers'):
  s=s.replace('Sgood5 one good5 source5 0 good5model','Sgood5 one good5 iso_en_pin 0 good5model')
  s=s.replace('Sgood5 one good5 rail5 0 good5model','Sgood5 one good5 iso_en_pin 0 good5model')
  lines=s.splitlines()
  lines=[f".model good5model SW(Ron=.01 Roff=1e12 Vt={(p.get('iso_en_rise',.7)+p.get('iso_en_fall',.6))/2} Vh={(p.get('iso_en_rise',.7)-p.get('iso_en_fall',.6))/2})"if line.startswith('.model good5model ')else line for line in lines]
  s='\n'.join(lines)+'\n'
  extra=f'''R162phys rail5 iso_en_pin {p.get('iso_en_top',470000)*p.get('iso_en_top_scale',1)}
R163phys iso_en_pin 0 {p.get('iso_en_bottom',100000)*p.get('iso_en_bottom_scale',1)}
Biso_en_leak iso_en_pin 0 I={{{p.get('iso_en_leak',.1e-6)}*clip(v(iso_en_pin),0,1)}}
Bsns_leak snsiso 0 I={{{p.get('sns_leak',.1e-6)}*clip(v(snsiso),0,1)}}
'''
  s=s.replace('.control',extra+'\n.control')
 if p.get('physical_input_caps'):
  # Explicit selected count of polymer capacitors and their R/L feed.
  line=next(q for q in s.splitlines()if q.startswith('C160 '))
  rline=next(q for q in s.splitlines()if q.startswith('R_C160 '))
  s=s.replace(line,'').replace(rline,'')
  cap=470e-6*p.get('input_poly_scale',1);esr=p.get('input_poly_esr',.025)
  extra=f'Rhold vin hold_l {p.get("input_route_R",.03)}\nLhold hold_l hold_bus {p.get("input_route_L",100e-9)}\n'
  for n in range(p.get('input_cap_count',3)):
   ident=str(162+n)if n<3 else 'extra'+str(n)
   extra+=f'R_C{ident} hold_bus c{ident} {esr}\nC{ident} c{ident} 0 {cap}\n'
  s=s.replace('.control',extra+'\n.control')
 for name in ['C127','C128','C_OTHER5']:
  line=next(q for q in s.splitlines()if q.startswith(name+' '));words=line.split();words[-1]=str(float(words[-1])*p.get('ceramic5',1));s=s.replace(line,' '.join(words))
 s=s.replace('VREF=1.2224938875305624 ',f"VREF={p.get('rail5_dc',4.908)/4.09} ")
 # An enabled TPS22953 conducts in BOTH directions. Slew control must not
 # accidentally create an ideal diode when the upstream rail falls.
 s=s.replace(f"min(1/{p.get('ron',.04)},max(v(slewiso,vin),0)*1e6)",f"(v(feediso,vin)<0 ? 1/{p.get('ron',.04)} : min(1/{p.get('ron',.04)},max(v(slewiso,vin),0)*1e6))")
 s=s.replace('R165 source disdrain ', 'VR165 source disfeed 0\nR165 disfeed disdrain ')
 if p.get('active_discharge'):
  s=s.replace(' i(Vpass)\n',' i(Vpass) v(en151) v(disg) v(disdrain) i(VR165)\n')
 s=s.replace(' v(PROTECTED_12V) ', ' v(switchon) v(restartage) v(snsevent) i(VR158) v(damped) v(PROTECTED_12V) ')
 if p.get('mode')=='off':s=s.replace('80m 12 80.1m 0','150m 12 150.1m 0')
 if p.get('mode')=='load':s=s.replace('75m .45 75.001m .75 85m .75 85.001m .02 95m .02 95.001m .45','150m .45 150.001m .75 160m .75 160.001m .02 170m .02 170.001m .45').replace('0.12 0 2e-06','0.2 0 2e-06')
 s=s.replace('.control', 'C161phys feediso 0 100n\n.control')
 if p.get('service3'):
  s=s.replace('R153 source main 0.01','R153 source main 1e12\nVservice3 main 0 PWL(0 0 1m 0 2m 3.3)')
  s=s.replace('R153 source main_feed 0.01','R153 source main_feed 1e12\nVservice3 main 0 PWL(0 0 1m 0 2m 3.3)')
 if p.get('release_zero'):s=s.replace('160.001m .02 170m .02','160.001m 0 170m 0')
 if p.get('bulk_switch'):
  # A second TPS22953-Q1 slews the reservoir itself. VIN/BIAS/SNS are at
  # the main rail; the precision EN divider waits until BIAS exceeds 2.5V.
  # SNS cannot fall while EN is valid because it senses the undivided input.
  s=s.replace(f"R158 branch_r damped {p['damp']}",f"R158 bulksw_out damped {p['damp']}")
  ex=f'''R169 bulk_en_in bulk_en_pin {p.get('bulk_en_top',30100)*p.get('bulk_en_top_scale',1)}
R170 bulk_en_pin 0 {p.get('bulk_en_bottom',10000)*p.get('bulk_en_bottom_scale',1)}
Rbulk_en_in main bulk_en_in .001
Bbulk_en_leak bulk_en_pin 0 I={{{p.get('bulk_en_leak',.1e-6)}*clip(v(bulk_en_pin),0,1)}}
Sbulk_en one bulk_want bulk_en_pin 0 bulk_enmodel
Rbulk_want bulk_want 0 1k
.model bulk_enmodel SW(Ron=.01 Roff=1e12 Vt={(p.get('bulk_en_rise',.7)+p.get('bulk_en_fall',.6))/2} Vh={(p.get('bulk_en_rise',.7)-p.get('bulk_en_fall',.6))/2})
Bbulk_delay 0 bulk_enabled I={{(v(bulk_want)-v(bulk_enabled))/{p.get('bulk_off_delay',100e-6)/.693147}}}
Cbulk_delay bulk_enabled 0 1 IC=0
Bbulk_age 0 bulk_age I={{v(bulk_enabled)>.5 ? 1 : -v(bulk_age)/1u}}
Cbulk_age bulk_age 0 1 IC=0
Rbulk_age bulk_age 0 1e12
Bbulk_slew bulk_slew 0 V={{min(max((v(bulk_age)-.0005)/{p.get('bulk_slew',.01157)},0),max(v(branch_r),0))}}
Vbulkpass branch_r bulk_feed 0
Bbulkpass bulk_feed bulksw_out I={{v(bulk_enabled)>.5 ? v(bulk_feed,bulksw_out)*(v(bulk_feed,bulksw_out)<0 ? 1/{p.get('bulk_ron',.06)} : min(1/{p.get('bulk_ron',.06)},max(v(bulk_slew,bulksw_out),0)*1e6)) : -100u*clip(v(bulksw_out),0,1)}}
Bbulk_bias main 0 I={{50u*clip(v(main),0,1)}}
Rbulk_localcap branch_r bulk_localcap .01
C167phys bulk_localcap 0 {1e-6*p.get('bulk_local_cap_scale',1)}
R168bleed damped 0 {p.get('bulk_bleed',1000)}
Bbulk_capleak damped 0 I={{{p.get('bulk_leak',0)}*clip(v(damped),0,1)}}
'''
  s=s.replace('.control',ex+'\n.control')
  s=s.replace('i(VR158) v(damped)','i(VR158) v(damped) i(Vbulkpass) v(bulksw_out) v(bulk_en_pin)')
 s=s.replace(' v(PROTECTED_12V) ', ' v(rail5) v(PROTECTED_12V) ')
 if p.get('load_start') and p.get('mode')=='load':
  start=p['load_start']
  s=s.replace('150m .45 150.001m .75 160m .75 160.001m .02 170m .02 170.001m .45',f'{start} .45 {start+1e-6} .75 {start+.01} .75 {start+.010001} .02 {start+.02} .02 {start+.020001} .45')
  s=s.replace('150m .45 150.001m .75 160m .75 160.001m 0 170m 0 170.001m .45',f'{start} .45 {start+1e-6} .75 {start+.01} .75 {start+.010001} 0 {start+.02} 0 {start+.020001} .45')
 if p.get('off_start') and p.get('mode')=='off':
  start=p['off_start'];again=p.get('reapply',start+.6)
  s=s.replace('150m 12 150.1m 0 750m 0 750.1m 12',f'{start} 12 {start+.0001} 0 {again} 0 {again+.0001} 12')
 if p.get('stop'):
  s='\n'.join(f"tran 2e-06 {p['stop']} 0 {p.get('max_step',2e-6)}"if q.startswith('tran ')else q for q in s.splitlines())+'\n'
 s=s.replace('echo I31_FINISHED','echo I32_FINISHED\necho I32_FINISHED > completion.txt')
 return s

def run_local(p,out):
 d=out/p['name'];d.mkdir(parents=True,exist_ok=False);s=build(p);(d/'case.cir').write_text(s);(d/'lm63615_derivative.lib').write_text(MODEL)
 try:
  proc=subprocess.run(['ngspice','-b','case.cir'],cwd=d,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=240);rc=proc.returncode;(d/'run.log').write_text(proc.stdout)
 except subprocess.TimeoutExpired as e:
  rc=None;(d/'run.log').write_text(str(e))
 r=dict(parameters=p,returncode=rc,deck_sha256=hashlib.sha256(s.encode()).hexdigest())
 try:
  x=np.genfromtxt(d/'waveform.tsv',names=True);t=x['time'];stop=p.get('stop',.85 if p.get('mode')=='off'else .2 if p.get('mode')=='load'else .12)
  log=(d/'run.log').read_text();assert rc==0 and (d/'completion.txt').read_text().strip()=='I32_FINISHED' and 'aborted'not in log.lower()and abs(t[-1]-stop)<1e-9 and all(np.isfinite(x[n]).all()for n in x.dtype.names)
  active=x['vready']>.5;valid=x['vsource']>.3;cur=x['iVR158'];pd=cur**2*p['damp'];r.update(completed=True,end_s=float(t[-1]),samples=len(t),main_peak_V=float(x['vmain'].max()),main_final_V=float(x['vmain'][-1]),active_min_V=float(x['vmain'][active].min())if active.any()else None,ready_final=float(x['vready'][-1]),minimum_vin_minus_output_V=float((x['vvin']-x['vsource'])[valid].min())if valid.any()else None,input_switch_peak_A=float(x['iVpass'].max()),input_switch_reverse_A=float(x['iVpass'].min()),I151_max_A=float(x['iL151'].max()),I121_max_A=float(x['iL121'].max()),ready_rises=int(((x['vready'][1:]>.5)&(x['vready'][:-1]<.5)).sum()),sns_faults=int(((x['vsnsevent'][1:]>.5)&(x['vsnsevent'][:-1]<.5)).sum()),R158_peak_W=float(pd.max()),R158_energy_J=float(np.trapz(pd,t)),R158_RMS_A=float(np.sqrt(np.trapz(cur**2,t)/t[-1])))
  
  r['rail5_active_range_V']=[float(x['vrail5'][active].min()),float(x['vrail5'][active].max())]if active.any()else None
  event=p.get('load_start',.15)if p.get('mode')=='load'else p.get('off_start',p.get('fault_start',.15))
  pre=(t>event-.01)&(t<event);r['pre_fault_ready']=bool(pre.any()and np.all(x['vready'][pre]>.5))if p.get('mode')in ['off','load']or p.get('sns_fault')or p.get('live_fault')else None
  r['pre_fault_main_min_V']=float(x['vmain'][pre].min())if pre.any()else None
  normal=(t>.10)&(t<.149);r['normal_main_min_V']=float(x['vmain'][normal].min())if normal.any()else None
  if 'iVR165'in x.dtype.names:
   di=x['iVR165'];dp=di**2*p.get('r165',4.7);r['R165']=dict(peak_A=float(di.max()),minimum_A=float(di.min()),peak_abs_A=float(abs(di).max()),peak_W=float(dp.max()),energy_J=float(np.trapz(dp,t)))
  from input_stress import resistor_screen
  if 'iVR165'in x.dtype.names:r['R165']['pulse_screen_125C']=resistor_screen(t,dp,1.5*30/85)
  r['source_peak_V']=float(x['vsource'].max())
  for label,current,voltage in [('U152','iVpass',x['vrail5']-x['vvin']),('U153','iVbulkpass',x['vmain']-x['vbulksw_out'] if 'vbulksw_out'in x.dtype.names else None)]:
   if current in x.dtype.names:
    watts=np.maximum(x[current]*voltage,0);r[label]=dict(peak_A=float(x[current].max()),reverse_A=float(x[current].min()),peak_W=float(watts.max()),energy_J=float(np.trapz(watts,t)),mean_W=float(np.trapz(watts,t)/t[-1]))
  if active.any():
   first=int(np.flatnonzero(active)[0]);r['first_ready_s']=float(t[first])
   r['unmasked_post_ready_min_V']=float(x['vmain'][first:].min())
  if p.get('mode')=='load':
   runwindow=t>event-.01;r['load_window_min_V']=float(x['vmain'][runwindow].min());r['load_window_peak_V']=float(x['vmain'][runwindow].max())
  r['waveform_sha256']=hashlib.sha256((d/'waveform.tsv').read_bytes()).hexdigest()
  stride=max(1,len(x)//4000);np.savetxt(d/'trace.csv',np.column_stack([x[n][::stride]for n in x.dtype.names]),delimiter=',',header=','.join(x.dtype.names),comments='')
  raw=d/'waveform.tsv';packed=d/'waveform.tsv.gz'
  with raw.open('rb')as f,gzip.open(packed,'wb',compresslevel=1)as z:shutil.copyfileobj(f,z)
  with gzip.open(packed,'rb')as f:assert hashlib.file_digest(f,'sha256').hexdigest()==r['waveform_sha256']
  raw.unlink()
 except Exception as e:r.update(completed=False,error=str(e))
 (d/'RESULT.json').write_text(json.dumps(r,indent=2)+'\n');print(p['name'],r,flush=True);return r

def run(p,out):
 # Keep the large intermediate TSV outside the synchronized artifact tree.
 # Publish only verified lossless records and exact replay inputs. Failed
 # simulations receive the same preservation, and a failed copy keeps staging.
 staging=Path(tempfile.mkdtemp(prefix='gr86_i32_power_'))
 result=run_local(p,staging);d=staging/p['name']
 raw=d/'waveform.tsv'
 if raw.exists():
  packed=d/'waveform.tsv.gz'
  with raw.open('rb')as f,gzip.open(packed,'wb',compresslevel=1)as z:shutil.copyfileobj(f,z)
  with raw.open('rb')as f:expected=hashlib.file_digest(f,'sha256').hexdigest()
  with gzip.open(packed,'rb')as f:assert hashlib.file_digest(f,'sha256').hexdigest()==expected
  raw.unlink()
 target=out/p['name'];target.mkdir(parents=True,exist_ok=False)
 for f in d.iterdir():
  if not f.is_file():continue
  dest=target/f.name
  with f.open('rb')as src,dest.open('wb')as dst:shutil.copyfileobj(src,dst)
  with f.open('rb')as src,dest.open('rb')as dst:assert hashlib.file_digest(src,'sha256').digest()==hashlib.file_digest(dst,'sha256').digest()
 shutil.rmtree(staging)
 return result

def cases():
 base=dict(bulk=470,damp=.47,top=11300,bleed=330)
 ps=[dict(name='nominal'),dict(name='slow',slow=True),dict(name='load_release',mode='load'),dict(name='cold_loaded_450mA',constant=.45),dict(name='cold_loaded_750mA',constant=.75,ipos=1.55),dict(name='off_restart',mode='off'),dict(name='sns_restart',sns_fault=True),dict(name='external5',external5=True)]
 return [dict(base,**p)for p in ps]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--cases',type=Path);ap.add_argument('--jobs',type=int,default=4);a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
 ps=json.loads((a.cases or D/'POWER_CASES.json').read_text())
 with cf.ThreadPoolExecutor(a.jobs)as pool:rr=list(pool.map(lambda p:run(p,a.output),ps))
 (a.output/'RESULTS.json').write_text(json.dumps(rr,indent=2)+'\n')
if __name__=='__main__':main()
