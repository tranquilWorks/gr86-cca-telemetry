"""Isolated U151 supplier-model test; not a whole-board or automotive qualification.
The caller supplies an authorized private model path. Supplier contents are never
copied to outputs. Netlists, derived waveforms, hashes and limited diagnostics only.
"""
from __future__ import annotations
import argparse, hashlib, json, pathlib, re, shutil, subprocess, tempfile, time
from concurrent.futures import ThreadPoolExecutor
import numpy as np


def rawdata(path):
    with path.open('rb') as stream:
        header=bytearray()
        while True:
            line=stream.readline()
            if not line: raise ValueError('No binary data header')
            header.extend(line)
            if line.strip()==b'Binary:': break
        text=header.decode(errors='replace'); offset=stream.tell()
    nv=int(re.search(r'No. Variables:\s*(\d+)',text)[1])
    npnt=int(re.search(r'No. Points:\s*(\d+)',text)[1])
    names=re.findall(r'^\s*\d+\s+(\S+)\s+\S+',text.split('Variables:',1)[1],re.M)
    if path.stat().st_size != offset+8*nv*npnt: raise ValueError('Incomplete raw file')
    array=np.memmap(path,dtype='<f8',mode='r',offset=offset,shape=(npnt,nv))
    return {name:array[:,i] for i,name in enumerate(names)}


def circuit(name,bulk,ceramic,preload,runload,stop,delay):
    return f'''I28 U151 supplier-model stage screen {name}; not whole board
.include "supplier.lib"
* Finite-resistance 5V test supply, NOT the U121 converter or vehicle input.
Vrail ext 0 PWL(0 0 100u 0 200u 5)
Rfeed ext vin .05
C151 vin 0 {22e-6*ceramic}
C152 vin 0 {0.22e-6*ceramic}
C153 vcc 0 1u
C154 boot sw .22u
R157 vsel 0 10k
XU151 0 boot vin fb nc 0 0 0 pg vcc sw sw vcc vcc vin vin vsel LM63615-Q1_TRANS PARAMS: SS=0 FASTSS=0
L151 sw ind 15u
Rdcr ind src .0771
R155 src fb 11.8k
R156 fb 0 4.99k
C155 src ce1 {22e-6*ceramic}
Re1 ce1 0 .005
C156 src ce2 {22e-6*ceramic}
Re2 ce2 0 .005
C157 src ce3 {22e-6*ceramic}
Re3 ce3 0 .005
C158 src 0 {0.1e-6*ceramic}
R153 src main .01
CLOCAL main clocal {45.5e-6*ceramic}
Rclocal clocal 0 .005
R158 main bulk_node .082
C206 bulk_node bulk_esr {bulk}
Resr206 bulk_esr 0 .025
R154 main 0 1k
Rpg main pg 100k
* Deliberately early load stress. Actual TPS3808 reset/firmware boot NOT modeled.
Rpre main 0 {3.364729459/preload}
Irun main 0 PWL(0 0 {delay} 0 {delay+10e-6} {runload-preload})
.options reltol=1e-3 abstol=1e-9 vntol=1e-6 method=gear itl4=500
.save v(vin) v(main) v(src) v(fb) v(vcc) v(sw) v(pg) i(L151) i(Vrail)
.tran 25n {stop} 0 25n
.end
'''


def run(name,params,model,out):
    path=out/name; path.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='i28-model-') as td:
        work=pathlib.Path(td); shutil.copyfile(model,work/'supplier.lib')
        init='set ngbehavior=ps\n'
        for cm in pathlib.Path('/usr/lib/x86_64-linux-gnu/ngspice').glob('*.cm'):
            init+=f'codemodel {cm}\n'
        (work/'.spiceinit').write_text(init)
        deck=circuit(name,**params)
        (work/'run.cir').write_text(deck); (path/'circuit.cir').write_text(deck)
        begin=time.monotonic()
        try:
            proc=subprocess.run(['ngspice','-b','-r','result.raw','-o','solver.log','run.cir'],cwd=work,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=900)
            code=proc.returncode
        except subprocess.TimeoutExpired: code='timeout'
        text=(work/'solver.log').read_text(errors='replace') if (work/'solver.log').exists() else ''
        complete=code==0 and 'No. of Data Rows' in text and 'timestep too small' not in text.lower()
        # Never return echoed proprietary model source from a parser failure.
        errors=[line for line in text.splitlines() if line.lower().startswith(('error:', 'fatal error:', 'doanalyses:', 'timestep too small'))]
        result={'name':name,'engine_completed':complete,'returncode':code,'elapsed_s':time.monotonic()-begin,'parameters':params,'supplier_sha256':hashlib.sha256(model.read_bytes()).hexdigest(),'supplier_content_published':False,'deck_sha256':hashlib.sha256(deck.encode()).hexdigest(),'diagnostics':errors,'model_class':'TI_LM63615_Q1_TRANS_WITH_AUTHORED_TEST_FIXTURE','whole_board_pass':False,'automotive_qualified':False}
        if complete:
            data=rawdata(work/'result.raw'); t=data['time']; mask=t>=t[-1]-.001
            bounds=lambda v:{'min':float(v.min()),'max':float(v.max()),'final':float(v[-1])}
            result['duration_s']=float(t[-1]); result['raw_points']=len(t)
            result['bounds']={n:bounds(v) for n,v in data.items() if n!='time'}
            result['settled_last1ms']={n:bounds(v[mask]) for n,v in data.items() if n!='time'}
            result['stage_checks']={'settled_main_3p11605_to3p6':bool(np.all((data['v(main)'][mask]>=3.11605)&(data['v(main)'][mask]<=3.6))),'peak_main_below3p6':bool(data['v(main)'].max()<=3.6)}
            result['raw_sha256']=hashlib.sha256((work/'result.raw').read_bytes()).hexdigest()
            sampled_t=np.arange(t[0],t[-1],2e-6)
            values=np.column_stack([sampled_t]+[np.interp(sampled_t,t,v) for n,v in data.items() if n!='time'])
            np.savetxt(path/'overview.csv',values,delimiter=',',header=','.join(data),comments='',fmt='%.9g')
        (path/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result),flush=True)
        return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--model',type=pathlib.Path,required=True)
    ap.add_argument('--output',type=pathlib.Path,required=True)
    a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    cases={
      'U151_nominal_bank':dict(bulk=470e-6,ceramic=1.,preload=.05,runload=.45,stop=.008,delay=.004),
      'U151_max_bank':dict(bulk=806.52e-6,ceramic=1.25,preload=.05,runload=.45,stop=.008,delay=.004),
    }
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(run,n,p,a.model,a.output) for n,p in cases.items()]
        results=[f.result() for f in futures]
    (a.output/'SUMMARY.json').write_text(json.dumps({'results':results,'model_use':'Transient private computation; model not redistributed. No bench/vehicle evidence.'},indent=2)+'\n')
if __name__=='__main__': main()
