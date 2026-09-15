#!/usr/bin/env python3
"""Lumped input trajectory screen; topology from I31/current native netlist.

Q101 is an explicit Level-1 approximation, not an ST model. Its trajectory is
screened separately against conservatively read SOA curves. Published maximum
delay/current and pessimistic charge/clamp/cable parameters are explicit. This
does not simulate fuse interruption, semiconductor avalanche or qualification.
"""
from pathlib import Path
import argparse, concurrent.futures as cf, hashlib, json, subprocess, gzip, shutil
import numpy as np
D=Path(__file__).resolve().parent
BASE=(D.parent/'i31/nominal_cascade.cir').read_text().split('R125 VIN5')[0]

def deck(p):
 s=BASE.replace('I31 U151 derivative startup; not TI encrypted model','I32 input component trajectory, transparent approximation')
 s=s.replace('.include "lm63615_derivative.lib"','.func clip(x,a,b) {min(max(x,a),b)}')
 for old,new in [('CABLE_L=1u',f"CABLE_L={p.get('cable_L',10e-6)}"),('CABLE_R=.1',f"CABLE_R={p.get('cable_R',.1)}"),('CgsQ=910p',f"CgsQ={p.get('cgs',3.9e-9)}"),('CgdQ=100p',f"CgdQ={p.get('cgd',300e-12)}"),('CAP_SCALE=1',f"CAP_SCALE={p.get('cap_scale',.5)}"),('RDS_SCALE=1','RDS_SCALE=3.34'),('IUP=35u',f"IUP={p.get('iup',60e-6)}"),('OVREF=.5','OVREF=.5075'),('TON=32m','TON=22m'),('R101 REV_BLOCKED_12V PROTECT_CTRL_VIN 6.81k',f"R101 REV_BLOCKED_12V PROTECT_CTRL_VIN {p.get('r101',12100)}"),('Cdelay allow_d 0 2.885u',f"Cdelay allow_d 0 {p.get('delay',10e-6)/.693147}"),('0,0.06','0,0.03'),('Bctrl PROTECT_CTRL_VIN 0 I={30u','Bctrl PROTECT_CTRL_VIN 0 I={90u'),('Bctrlout PROTECTED_12V 0 I={40u','Bctrlout PROTECTED_12V 0 I={110u')]:s=s.replace(old,new)
 s=s.replace('VBAT BAT 0 PWL(0 0 1m 0 2m 12)','VBAT BAT 0 PWL('+p['pwl']+')')
 s=s.replace('D101 FUSED_12V REV_BLOCKED_12V d_small','VD101 FUSED_12V diode101 0\nD101 diode101 REV_BLOCKED_12V d_input\n.model d_input D(Is=1n N=1.3 Rs=.10 Cjo=100p)')
 s=s.replace('Rs=.10 Cjo=100p',f'Rs=.10 Cjo={p.get("diode_cj",100e-12)}')
 if p.get('pulse_resistance_interval'):
  lo,hi=p['pulse_resistance_interval'];s=s.replace('Rcable BAT cable_r {CABLE_R}',f'Rcable BAT cable_r R={{time>={lo} && time<={hi} ? CABLE_R : .1}}')
 s=s.replace('Cqds REV_BLOCKED_12V qsrc 167p',f'Cqds REV_BLOCKED_12V qsrc {p.get("coss",167e-12)}')
 s=s.replace('M_Q101 REV_BLOCKED_12V','VQ101 REV_BLOCKED_12V qdrain 0\nM_Q101 qdrain')
 s=s.replace('Cqgd INPUT_GATE REV_BLOCKED_12V','Cqgd INPUT_GATE qdrain').replace('Cqds REV_BLOCKED_12V','Cqds qdrain').replace('Dqbody qsrc REV_BLOCKED_12V','Dqbody qsrc qdrain')
 s=s.replace('BD103 PROTECTED_12V 0 I={max((v(PROTECTED_12V)-29.5)/0.244,0)}',f'VD103 PROTECTED_12V tvs103 0\nBD103 tvs103 0 I={{max((v(tvs103)-{29.5*p.get("clamp_scale",1.1)})/{.244*p.get("clamp_scale",1.1)},0)}}\nD103f 0 tvs103 d_small')
 s=s.replace('BD102 PROTECT_CTRL_VIN 0 I={max((v(PROTECT_CTRL_VIN)-36.8)/1.4,0)}','VD102 PROTECT_CTRL_VIN tvs102 0\nBD102 tvs102 0 I={max((v(tvs102)-40.5)/1.54,0)}\nD102f 0 tvs102 d_small')
 s=s.replace('BD104 INPUT_GATE PROTECTED_12V I={max((v(INPUT_GATE,PROTECTED_12V)-15)/2,0)}','VD104 INPUT_GATE clamp104 0\nBD104 clamp104 PROTECTED_12V I={max((v(clamp104,PROTECTED_12V)-15.6)/20,0)}')
 if p.get('snubber'):
  s+='R112 REV_BLOCKED_12V snub 33\nC104 snub 0 10n\n'
 if p.get('raw_clamp'):
  scale=1+.00107*(p.get('clamp_temperature_C',125)-25)
  br=(122 if p.get('clamp_minimum')else 135)*scale
  rd=(177-135)/8.5*scale
  s+=f'VD105 REV_BLOCKED_12V clamp105_wire 0\nL105 clamp105_wire clamp105_r {p.get("clamp_lead_L",100e-9)}\nR105lead clamp105_r clamp105 {p.get("clamp_lead_R",.06)}\nBD105 clamp105 0 I={{max((v(clamp105)-{br})/{rd},0)}}\nCD105 clamp105 0 {p.get("clamp_cj",300e-12)}\nD105f 0 clamp105 d_small\n'
 s+=f'Bload5 VIN5 0 I={{{p.get("load",.5)}*clip(v(VIN5)/5,0,1)}}\n'
 vectors='v(BAT) v(RAW_12V) v(FUSED_12V) v(REV_BLOCKED_12V) v(PROTECT_CTRL_VIN) v(INPUT_UV) v(INPUT_OV) v(INPUT_SHDN) v(INPUT_GATE_DRIVE) v(INPUT_GATE) v(PROTECTED_12V) v(VIN5) i(VQ101) i(VD101) i(VD102) i(VD103) i(VD104) i(Lcable) v(allow_d)'
 if p.get('raw_clamp'):vectors+=' v(clamp105) i(VD105)'
 s+=f'.options method=gear maxord=2 reltol=1e-4 abstol=1n vntol=1u\n.control\nset wr_vecnames\nset wr_singlescale\nsave {vectors}\ntran {p.get("step",1e-6)} {p["stop"]} 0 {p.get("step",1e-6)}\nwrdata waveform.tsv {vectors}\necho I32_FINISHED\nquit\n.endc\n.end\n'
 return s

def pulse_intervals(t, mask):
 # Include one adjacent sample at each boundary; durations are rounded upward.
 starts=np.flatnonzero(mask & ~np.r_[False,mask[:-1]])
 ends=np.flatnonzero(mask & ~np.r_[mask[1:],False])
 return [(max(0,int(a)-1),min(len(t)-1,int(b)+1)) for a,b in zip(starts,ends)]

def resistor_screen(t,power,continuous_W):
 pulses=[]
 for a,b in pulse_intervals(t,power>continuous_W):
  pulses.append(dict(start_s=float(t[a]),duration_s=float(t[b]-t[a]),peak_W=float(power[a:b+1].max()),energy_J=float(np.trapz(power[a:b+1],t[a:b+1]))))
 return dict(continuous_derated_W=continuous_W,whole_record_mean_W=float(np.trapz(power,t)/(t[-1]-t[0])),pulses_above_continuous=pulses)

def run(p,out):
 d=out/p['name'];d.mkdir(parents=True,exist_ok=False);s=deck(p);(d/'case.cir').write_text(s)
 with (d/'run.log').open('w')as f:
  try:rc=subprocess.run(['ngspice','-b','case.cir'],cwd=d,stdout=f,stderr=subprocess.STDOUT,timeout=180).returncode
  except subprocess.TimeoutExpired:rc=None
 r=dict(parameters=p,returncode=rc,deck_sha256=hashlib.sha256(s.encode()).hexdigest())
 try:
  x=np.genfromtxt(d/'waveform.tsv',names=True);t=x['time'];v=lambda n:x['v'+n];i=lambda n:x['i'+n]
  log=(d/'run.log').read_text();assert rc==0 and 'I32_FINISHED'in log and 'aborted'not in log.lower() and abs(t[-1]-p['stop'])<1e-9 and all(np.isfinite(x[n]).all()for n in x.dtype.names)
  vd=v('REV_BLOCKED_12V')-v('PROTECTED_12V');vg=v('INPUT_GATE')-v('PROTECTED_12V');iq=i('VQ101');pd=np.maximum(vd*iq,0)
  r.update(completed=True,end_s=float(t[-1]),samples=len(t),Q101_VDS_max_V=float(vd.max()),Q101_VGS_max_V=float(vg.max()),Q101_VGS_min_V=float(vg.min()),Q101_current_peak_A=float(iq.max()),Q101_energy_positive_J=float(np.trapz(pd,t)),Q101_power_peak_W=float(pd.max()),D101_reverse_max_V=float((v('REV_BLOCKED_12V')-v('FUSED_12V')).max()),D101_current_peak_A=float(i('VD101').max()),fuse_I2t_A2s=float(np.trapz(i('VD101')**2,t)),R101_peak_V=float((v('REV_BLOCKED_12V')-v('PROTECT_CTRL_VIN')).max()),R101_peak_W=float(((v('REV_BLOCKED_12V')-v('PROTECT_CTRL_VIN'))**2/p.get('r101',12100)).max()),R101_energy_J=float(np.trapz((v('REV_BLOCKED_12V')-v('PROTECT_CTRL_VIN'))**2/p.get('r101',12100),t)),R110_peak_W=float(((v('PROTECTED_12V')-v('VIN5'))**2/.475).max()),R110_energy_J=float(np.trapz((v('PROTECTED_12V')-v('VIN5'))**2/.475,t)))
  for n in ['PROTECT_CTRL_VIN','INPUT_UV','INPUT_OV','INPUT_SHDN','INPUT_GATE_DRIVE','PROTECTED_12V','VIN5','RAW_12V','REV_BLOCKED_12V']:r[n+'_range_V']=[float(v(n).min()),float(v(n).max())]
  for n,vn in [('D102','PROTECT_CTRL_VIN'),('D103','PROTECTED_12V'),('D104','INPUT_GATE')]:
   vv=vg if n=='D104'else v(vn);cur=i('V'+n);power=np.maximum(vv*cur,0)
   r[n]=dict(peak_A=float(cur.max()),peak_W=float(power.max()),positive_energy_J=float(np.trapz(power,t)),charge_C=float(np.trapz(np.maximum(cur,0),t)),duration_above_1mA_s=float(np.trapz((cur>.001).astype(float),t)))
  if p.get('raw_clamp'):
   cur=i('VD105');power=np.maximum(v('clamp105')*cur,0)
   r['D105']=dict(peak_A=float(cur.max()),peak_W=float(power.max()),positive_energy_J=float(np.trapz(power,t)),duration_above_1mA_s=float(np.trapz((cur>.001).astype(float),t)),terminal_max_V=float(v('clamp105').max()))
  # SOA uses the actual contiguous linear-operation interval, including
  # adjacent samples. Round UP to a published pulse family, never extend a
  # short-pulse curve into an invented DC SOA. On-state conduction is separate.
  events=[];scale=(175-p.get('case_temperature_C',125))/150
  for event in p['events']:
   label,lo,hi=event[:3];m=(t>=lo)&(t<=hi)
   segments=[]
   for aa,bb in pulse_intervals(t,m&(vd>1)&(iq>.01)):
    dt=float(t[bb]-t[aa]);families=[(1e-5,6000),(1e-4,2400),(1e-3,600),(1e-2,240)]
    selected=next(((duration,power)for duration,power in families if dt<=duration),None)
    rr=dict(duration_s=dt,start_s=float(t[aa]),peak_VDS_V=float(vd[aa:bb+1].max()),peak_ID_A=float(iq[aa:bb+1].max()),positive_energy_J=float(np.trapz(pd[aa:bb+1],t[aa:bb+1])))
    if selected:
     duration,power=selected;limit=np.minimum(60,power/np.maximum(vd[aa:bb+1],.01))*scale
     rr.update(published_family_s=duration,derated_SOA_utilization_max=float((np.maximum(iq[aa:bb+1],0)/limit).max()),status='SCREENED_PUBLISHED_PULSE_FAMILY')
    else:rr.update(status='OUTSIDE_PUBLISHED_SOA_FAMILIES')
    segments.append(rr)
   events.append(dict(event=label,linear_intervals=segments,positive_energy_J=float(np.trapz(pd[m],t[m])),fuse_event_I2t_A2s=float(np.trapz(i('VD101')[m]**2,t[m])),SOA_scope='Fig.2 lower-bound trajectory screen at allocated case temperature; no avalanche or DC extrapolation'))
  r['Q101_case_temperature_allocation_C']=p.get('case_temperature_C',125)
  r['Q101_onstate_power_max_W']=float(pd[vd<=1].max())
  r['R101_pulse_screen']=resistor_screen(t,(v('REV_BLOCKED_12V')-v('PROTECT_CTRL_VIN'))**2/p.get('r101',12100),(155-p.get('case_temperature_C',125))/85)
  r['R110_pulse_screen']=resistor_screen(t,(v('PROTECTED_12V')-v('VIN5'))**2/.475,.8*(170-p.get('case_temperature_C',125))/100)
  r['events']=events;r['waveform_sha256']=hashlib.sha256((d/'waveform.tsv').read_bytes()).hexdigest()
  # A compact trace is for plots only; extrema are from every full-resolution row.
  stride=max(1,len(x)//3000);names=x.dtype.names
  np.savetxt(d/'trace.csv',np.column_stack([x[n][::stride]for n in names]),delimiter=',',header=','.join(names),comments='')
 except Exception as e:r.update(completed=False,error=str(e))
 if r.get('completed'):
  raw=d/'waveform.tsv';packed=d/'waveform.tsv.gz'
  with raw.open('rb')as f,gzip.open(packed,'wb',compresslevel=1)as z:shutil.copyfileobj(f,z)
  with gzip.open(packed,'rb')as f:assert hashlib.file_digest(f,'sha256').hexdigest()==r['waveform_sha256']
  raw.unlink()
 (d/'RESULT.json').write_text(json.dumps(r,indent=2)+'\n');return r

def cases():
 common='0 0 1m 0 2m 12 '
 ps=[]
 for load in [0,.5]:
  ps.append(dict(name=f'startup_load{load}',pwl=common,stop=.08,load=load,cap_scale=1.2,events=[['inrush',.020,.05,.03]]))
 ps += [
  dict(name='load_dump_100V_400ms',pwl=common+'60m 12 65m 100 465m 100 470m 12',stop=.53,step=2e-6,cable_R=2,events=[['fault',.06,.067,.01],['reconnect',.47,.52,.05]]),
  dict(name='fast_positive_50V_50us',pwl=common+'60m 12 60.001m 50 60.051m 50 60.052m 12',stop=.1,step=2e-7,cable_R=2,events=[['fault',.06,.06008,.0001]]),
  dict(name='negative_150V_2ms',pwl=common+'60m 12 60.001m -150 62.001m -150 62.002m 12',stop=.12,step=5e-7,cable_R=10,events=[['negative',.06,.063,.003]]),
  dict(name='reverse_14V',pwl='0 -14 60m -14 61m 12',stop=.13,events=[['recovery',.060,.12,.06]]),
  dict(name='jump_24V',pwl=common+'60m 12 61m 24 100m 24 101m 12',stop=.16,events=[['OV',.060,.065,.005],['reconnect',.101,.15,.05]]),
  dict(name='crank_6V',pwl=common+'60m 12 60.1m 6 90m 6 91m 12',stop=.15,events=[['UV',.06,.061,.001],['reconnect',.091,.14,.05]]),
 ]
 for snub in [False,True]:
  ps.append(dict(name='outside_contract_100V_1us'+('_RC_trial'if snub else''),pwl=common+'60m 12 60.001m 100 60.051m 100 60.052m 12',stop=.1,step=1e-7,cable_R=.1,snubber=snub,events=[['fault',.06,.06008,.0001]],outside_contract=True))
 return ps

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--jobs',type=int,default=4);ap.add_argument('--cases',type=Path,default=D/'INPUT_CASES.json');a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
 with cf.ThreadPoolExecutor(a.jobs)as pool:rr=list(pool.map(lambda p:run(p,a.output),json.loads(a.cases.read_text())))
 (a.output/'RESULTS.json').write_text(json.dumps(rr,indent=2)+'\n')
 for r in rr:print(r['parameters']['name'],r.get('completed'),{k:r.get(k)for k in ['Q101_VDS_max_V','Q101_current_peak_A','Q101_power_peak_W','PROTECTED_12V_range_V','D101_reverse_max_V','R101_peak_W']})
if __name__=='__main__':main()
