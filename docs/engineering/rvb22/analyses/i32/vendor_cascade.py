#!/usr/bin/env python3
"""Historical170-part U121/U152/U151 trial, with unchanged TI LM5164-Q1 model.

The fixture supplies U121 at VIN5 directly, separating the independently screened
automotive protection stage. U152 and U151 retain their disclosed approximations.
No time compression, precharged reservoir, or forced enable is used. This
retained trial is not a generator for the selected177-part acceptance circuit;
its archived deck controls exact replay.
"""
from pathlib import Path
import argparse, hashlib, json, shutil, subprocess, re
import numpy as np
import power_chain as pc

VENDOR_SHA = 'e11ddf6995163f98eda6205de6a7cb74c8a3982b7328467de8d806286e894b5d'

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--vendor-model',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--stop',type=float,default=.024)
    ap.add_argument('--solver',choices=['gear','trap','gear_stabilized'],default='gear')
    ap.add_argument('--ngspice',default='ngspice')
    a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=False)
    assert hashlib.sha256(a.vendor_model.read_bytes()).hexdigest()==VENDOR_SHA
    p=next(x for x in json.loads((pc.D/'POWER_CASES.json').read_text()) if x['name']=='combined_loaded_high_drive_low5')
    body=pc.build(p).split('R125 VIN5')[1].split('.control')[0]
    body='R125 VIN5'+body
    body=re.sub(r'^XU121 VIN5[^\n]*\n\+[^\n]*\n', 'R121 ron5 0 31.6k\nC124 bst5 sw5 2.2n\nR127 source5 pg5 100k\nXU121 bst5 EN5 fb5 0 0 pg5 ron5 sw5 VIN5 LM5164-Q1_TRANS\n', body, flags=re.M)
    body=re.sub(r'^\.options[^\n]*\n','',body,flags=re.M)
    assert all(x in body for x in ['C162 c162','C163 c163','C164 c164','R164gate','C161phys','R162phys','C165en'])
    assert 'XU121 bst5' in body and 'XU121 VIN5' not in body
    vectors='v(VIN5) v(source5) v(rail5) v(vin) v(source) v(main) i(L121) i(L151) i(Vpass) v(enable) v(en151) v(switchon) v(snsevent)'
    s='I32 closed vendor U121 cascade, constant 750mA startup\n.include "LM5164-Q1_TRANS.LIB"\n.include "lm63615_derivative.lib"\nVlogic one 0 1\nVINPUT inlet5 0 PWL(0 0 100u 0 200u 10.688)\nRfixture inlet5 VIN5 .1\nC121 VIN5 0 1.1u\nC122 VIN5 0 1.1u\nC123 VIN5 0 50n\nC129 VIN5 0 1.1u\n'+body
    # Solver stabilization is explicit and does not modify the TI library.
    # 1 fF / 1 Tohm node shunts are numerical conditioning, far below its
    # 1.4427 nF one-shot storage; their effect requires result comparison.
    stabilization=' rshunt=1e12 cshunt=1e-15 itl4=200' if a.solver!='gear' else ''
    method='gear' if a.solver=='gear_stabilized' else a.solver
    s+=f'\n.options method={method} maxord=2 reltol=.002 abstol=1n vntol=1u{stabilization}\n.control\nset filetype=binary\nsave {vectors}\ntran 50n {a.stop} 0 50n\nwrite waveform.raw {vectors}\necho I32_VENDOR_FINISHED > completion.txt\nquit\n.endc\n.end\n'
    (a.output/'case.cir').write_text(s)
    (a.output/'.spiceinit').write_text('set ngbehavior=ps\n')
    (a.output/'lm63615_derivative.lib').write_text(pc.MODEL)
    shutil.copyfile(a.vendor_model,a.output/'LM5164-Q1_TRANS.LIB')
    (a.output/'PARAMETERS.json').write_text(json.dumps(p,indent=2)+'\n')
    (a.output/'SIMULATOR_VERSION.txt').write_text(subprocess.check_output([a.ngspice,'--version'],text=True))
    with (a.output/'run.log').open('w') as log:
        proc=subprocess.run([a.ngspice,'-b','case.cir'],cwd=a.output,stdout=log,stderr=subprocess.STDOUT,timeout=3600)
    raw=a.output/'waveform.raw'; head=[]
    with raw.open('rb') as f:
        while True:
            line=f.readline(); assert line, 'missing binary header'
            head.append(line.decode().rstrip())
            if line.strip()==b'Binary:': offset=f.tell();break
    nv=int(next(s.split(':')[1] for s in head if s.startswith('No. Variables:')))
    nr=int(next(s.split(':')[1] for s in head if s.startswith('No. Points:')))
    i=head.index('Variables:'); names=[s.split()[1] for s in head[i+1:i+1+nv]]
    x=np.memmap(raw,dtype='<f8',mode='r',offset=offset,shape=(nr,nv)); t=x[:,0]
    v=lambda name: x[:,names.index(name)]
    finite=bool(np.isfinite(x).all())
    complete=proc.returncode==0 and (a.output/'completion.txt').exists() and (a.output/'completion.txt').read_text().strip()=='I32_VENDOR_FINISHED'
    complete=complete and 'aborted'not in (a.output/'run.log').read_text().lower() and abs(t[-1]-a.stop)<1e-10 and finite
    if not complete:
        with raw.open('rb')as f:raw_hash=hashlib.file_digest(f,'sha256').hexdigest()
        r=dict(status='ABORTED_NOT_STARTUP_PROOF',requested_stop_s=a.stop,end_s=float(t[-1]),samples=nr,finite=finite,
            returncode=proc.returncode,full_waveform_sha256=raw_hash,vendor_model_sha256=VENDOR_SHA,deck_sha256=hashlib.sha256(s.encode()).hexdigest(),scope=__doc__)
        np.savetxt(a.output/'trace.csv',x[::max(1,nr//6000)],delimiter=',',header=','.join(names),comments='')
        (a.output/'RESULT.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2),flush=True)
        raise SystemExit(2)
    late=t>a.stop-.002; valid=v('v(source)')>.3
    r=dict(status='COMPLETED_VENDOR_CLOSED_CASCADE',scope=__doc__,vendor_model_sha256=VENDOR_SHA,
           deck_sha256=hashlib.sha256(s.encode()).hexdigest(),end_s=float(t[-1]),samples=nr,
           source_peak_V=float(v('v(source)').max()),main_peak_V=float(v('v(main)').max()),
           late_main_range_V=[float(v('v(main)')[late].min()),float(v('v(main)')[late].max())],
           late_5V_range_V=[float(v('v(rail5)')[late].min()),float(v('v(rail5)')[late].max())],
           minimum_vin_minus_output_V=float((v('v(vin)')-v('v(source)'))[valid].min()),
           U121_peak_A=float(v('i(l121)').max()),U151_peak_A=float(v('i(l151)').max()),
           sns_faults=int(((v('v(snsevent)')[1:]>.5)&(v('v(snsevent)')[:-1]<.5)).sum()))
    h=hashlib.sha256()
    with raw.open('rb') as f:
        while chunk:=f.read(1048576):h.update(chunk)
    r['full_waveform_sha256']=h.hexdigest()
    np.savetxt(a.output/'trace.csv',x[::max(1,nr//6000)],delimiter=',',header=','.join(names),comments='')
    (a.output/'RESULT.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2),flush=True)

if __name__=='__main__':main()
