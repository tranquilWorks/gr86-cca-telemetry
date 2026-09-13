#!/usr/bin/env python3
"""Replay the I30 architecture-derived U121 SPICE experiments.

No manufacturer macromodel, whole-board release, or physical test is implied.
Requires Python 3.10+, NumPy 2.x, and ngspice with its matching XSPICE library.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, re, subprocess, time
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent

def value(text: str) -> float:
    m=re.match(r'(\d+(?:\.\d+)?)([A-Za-z]*)',text)
    if not m: raise ValueError(f'Unrecognized passive value: {text!r}')
    scale={'':1,'R':1,'k':1e3,'u':1e-6,'n':1e-9,'p':1e-12,'mR':1e-3}
    return float(m[1])*scale[m[2]]

def net(name: str) -> str:
    return '0' if name=='GND' else 'n_'+re.sub('[^A-Za-z0-9_]','_',name)

def build(c: dict, spec: dict) -> str:
    c=copy.deepcopy(c)
    if spec.get('negative_control'):
        c['R122']['value']='618k SIMULATION_NEGATIVE_CONTROL_ONLY'
    vin=spec.get('vin',10.6877); load=spec.get('load',.4665375)
    stop=spec.get('stop',.008); dt=spec.get('maxstep',20e-9)
    cs=spec.get('cap_scale',1.0); ls=spec.get('lscale',1.0); rs=spec.get('rscale',1.0)
    lines=[spec['name']+' : ARCHITECTURE-DERIVED SPICE; NOT VENDOR SIGNOFF',
      f'.include "{(HERE/"cot_derived.lib").as_posix()}"',
      '.options method=gear reltol=1e-4 abstol=1e-10 vntol=1e-7 itl4=100',
      f'Vfixture vin0 0 PWL(0 0 50u {vin} {stop} {vin})',
      'Rfixture vin0 n_5V_VIN .01']
    for ref in ['R122','R123','R124','R125','R126','R128','C121','C122','C123','C129','C125','C126','C127','C128']:
        comp=c[ref];a,b=[net(comp['pins'][n]) for n in ['1','2']];v=value(comp['value'])
        if ref.startswith('R'):
            lines.append(f'{ref} {a} {b} {max(.001,v):.12g}')
        else:
            if v>=1e-6:v*=cs
            esr=.005*rs if v>=1e-6 else .01
            lines.extend([f'RESR_{ref} {a} {a}_{ref} {esr:.12g}',f'{ref} {a}_{ref} {b} {v:.12g} ic=0'])
    lines.extend([
      f'L121 n_5V_SW lmid {value(c["L121"]["value"])*ls:.12g} ic=0',
      f'RL121 lmid n_5V_SOURCE {.134*rs:.12g}',
      'Bimon imon 0 V={i(L121)}',
      f'XU121 n_5V_VIN n_5V_SW n_5V_FB n_5V_EN imon COT_DERIVED ron={value(c["R121"]["value"])} ss={spec.get("ss",.003)} vref={spec.get("vref",1.2)} hs={.725*rs} ls={.34*rs}',
      f'Rfixture_load n__5V 0 {5/load:.12g}'])
    if 'step_load' in spec:
        lines.append('Bstep n__5V 0 I={time<4m ? 0 : (time<4.01m ? (time-4m)/10u : 1)*'+str(spec['step_load'])+'*min(max(v(n__5V),0),1)}')
    lines.extend(['.control','set wr_singlescale','set wr_vecnames',
      f'tran {dt:.12g} {stop:.12g} 0 {dt:.12g} uic',
      'wrdata waveform.txt v(n_5V_VIN) v(n__5V) v(n_5V_FB) i(L121) v(xu121.pwm) v(xu121.soft) i(Vfixture)',
      'quit','.endc','.end'])
    return '\n'.join(lines)+'\n'

def evaluate(case: Path, spec: dict, process: subprocess.CompletedProcess) -> dict:
    log=process.stdout+process.stderr
    (case/'engine.log').write_text(log)
    result={'name':spec['name'],'requested_stop_s':spec.get('stop',.008),'completed':False}
    wave=case/'waveform.txt'
    if not wave.is_file():
        result['error']='No waveform produced';return result
    a=np.loadtxt(wave,skiprows=1)
    if a.ndim!=2 or a.shape[1]!=8 or not np.isfinite(a).all():
        result['error']='Invalid waveform shape or nonfinite values';return result
    result['actual_stop_s']=float(a[-1,0]);result['points']=len(a)
    complete=(process.returncode==0 and a[-1,0]>=result['requested_stop_s']*(1-1e-7)
              and not re.search('timestep too small|simulation interrupted|fatal error|aborted',log,re.I))
    result['completed']=bool(complete)
    if not complete:
        result['error']='Incomplete transient; partial/post-abort measurements rejected';return result
    s=a[:,0]>result['requested_stop_s']-.001;t=a[s,0]
    mean=lambda x:float(np.trapezoid(x,t)/(t[-1]-t[0]))
    result.update(mean_output_V=mean(a[s,2]),steady_min_output_V=float(a[s,2].min()),
      steady_max_output_V=float(a[s,2].max()),peak_output_V=float(a[:,2].max()),
      peak_inductor_A=float(a[:,4].max()),steady_FB_ripple_Vpp=float(np.ptp(a[s,3])))
    if spec.get('negative_control'):
        expected=result['mean_output_V']>5.25
        result['expected_behavior']='Intentionally wrong R122 must produce detectable overvoltage'
    elif spec.get('vin')==7:
        expected=result['peak_output_V']<.1
        result['expected_behavior']='External EN divider keeps buck off at 7V fixture input'
    else:
        expected=4.75<=result['steady_min_output_V']<=result['steady_max_output_V']<=5.25
        expected=expected and result['peak_output_V']<=5.25 and result['peak_inductor_A']<1.25
        if 'step_load' in spec:expected=expected and float(a[a[:,0]>=.004,2].min())>=4.75
        result['expected_behavior']='Scoped voltage/current screen only; not full-board signoff'
    result['expected_model_behavior_observed']=bool(expected)
    return result

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ngspice',type=Path,required=True)
    p.add_argument('--code-model-dir',type=Path,help='Directory containing analog.cm; omit for a correctly installed system ngspice')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--case',help='Run only the exact named case from CASES.json')
    args=p.parse_args();engine=args.ngspice.resolve()
    if not engine.is_file():p.error('ngspice executable does not exist')
    args.output.mkdir(parents=True,exist_ok=False)
    source=json.loads((HERE/'SOURCE_COMPONENTS.json').read_text())
    if source['components']['U121']['mpn']!='LM5164QDDARQ1':raise ValueError('Wrong U121 source')
    cases=json.loads((HERE/'CASES.json').read_text())
    if args.case:
        cases=[c for c in cases if c['name']==args.case]
        if not cases:raise ValueError('Unknown case')
    results=[]
    for spec in cases:
        case=args.output/spec['name'];case.mkdir()
        (case/'case.cir').write_text(build(source['components'],spec))
        if args.code_model_dir:
            cm=(args.code_model_dir/'analog.cm').resolve()
            if not cm.is_file():raise FileNotFoundError(cm)
            if any(x.isspace() for x in cm.as_posix()):raise ValueError('Use an XSPICE library path without spaces for this ngspice command')
            (case/'.spiceinit').write_text(f'codemodel {cm.as_posix()}\n')
        started=time.monotonic()
        try:
            proc=subprocess.run([str(engine),'-b','case.cir'],cwd=case,text=True,capture_output=True,timeout=300)
            result=evaluate(case,spec,proc)
        except subprocess.TimeoutExpired:
            result={'name':spec['name'],'completed':False,'error':'Execution exceeded 300s; not accepted'}
        result['elapsed_s']=time.monotonic()-started
        (case/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        results.append(result);print(json.dumps(result),flush=True)
    report={'engine':str(engine),'source':source['binding'],'full_board_signoff':False,'physical_tests':0,'results':results,
      'input_file_sha256':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['SOURCE_COMPONENTS.json','CASES.json','cot_derived.lib']}}
    (args.output/'EXECUTION.json').write_text(json.dumps(report,indent=2)+'\n')
    return 0 if all(r.get('completed') and r.get('expected_model_behavior_observed') for r in results) else 1
if __name__=='__main__':raise SystemExit(main())
