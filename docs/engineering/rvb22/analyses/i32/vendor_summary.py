#!/usr/bin/env python3
"""Inspect complete or aborted TI-model binary records without claiming completion."""
from pathlib import Path
import argparse,gzip,hashlib,json,re
import numpy as np

def inspect(d,requested_stop=.024):
    raw=d/'waveform.raw.gz';digest=hashlib.sha256();head=[]
    with gzip.open(raw,'rb')as f:
        while True:
            line=f.readline();assert line;digest.update(line);head.append(line.decode().rstrip())
            if line.strip()==b'Binary:':break
        nv=int(next(s.split(':')[1]for s in head if s.startswith('No. Variables:')))
        nr=int(next(s.split(':')[1]for s in head if s.startswith('No. Points:')))
        ix=head.index('Variables:');names=[s.split()[1]for s in head[ix+1:ix+1+nv]]
        seen=0;finite=True;mins=np.full(nv,np.inf);maxs=-mins;trace=[];stride=max(1,nr//6000)
        while chunk:=f.read(nv*8*100000):
            digest.update(chunk);assert len(chunk)%(nv*8)==0
            x=np.frombuffer(chunk,dtype='<f8').reshape(-1,nv);finite=finite and bool(np.isfinite(x).all())
            mins=np.minimum(mins,x.min(axis=0));maxs=np.maximum(maxs,x.max(axis=0))
            first=(-seen)%stride;trace.append(x[first::stride].copy());seen+=len(x);last=x[-1].copy()
    assert seen==nr
    log=(d/'run.log').read_text();aborted='aborted'in log.lower()
    completed=finite and abs(last[0]-requested_stop)<1e-10 and not aborted
    failures=[line for line in log.splitlines()if any(s in line.lower()for s in ['timestep too small','aborted','internal timestep'])]
    out=dict(status='COMPLETED'if completed else'ABORTED_NOT_STARTUP_PROOF',requested_stop_s=requested_stop,
        end_s=float(last[0]),finite=finite,samples=seen,columns=names,
        full_waveform_sha256=digest.hexdigest(),extrema={n:dict(min=float(a),max=float(b),last=float(c))for n,a,b,c in zip(names,mins,maxs,last)},
        failure_log_lines=failures,scope='Historical I32 170-part, three-input-cap/330uF trial. Unmodified TI LM5164 library; downstream controller derivative. Not the selected177-part source.',
        files_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in d.iterdir()if p.is_file()and p.suffix in ['.cir','.lib','.LIB','.log','.txt']})
    np.savetxt(d/'trace.csv',np.concatenate(trace),delimiter=',',header=','.join(names),comments='')
    (d/'RESULT.json').write_text(json.dumps(out,indent=2)+'\n')
    print(d.name,out['status'],seen,out['end_s'],failures[-3:],flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('directories',type=Path,nargs='+');a=ap.parse_args()
    for d in a.directories:inspect(d)
