#!/usr/bin/env python3
"""Verify committed I32 evidence and package bytes without publishing or operating hardware."""
from pathlib import Path
import argparse, hashlib, json, os, subprocess, sys
D=Path(__file__).resolve().parent
W=D.parents[2]
ROOT=W.parents[2]

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):
            h.update(block)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    inventory=json.loads((D/'CHANGED_PATHS.json').read_text())
    for row in inventory['files']:
        path=ROOT/row['path']
        if row['action']=='D':
            assert not path.exists(),row['path']
        else:
            assert path.stat().st_size==row['bytes'] and sha(path)==row['sha256'],row['path']
    binding=json.loads((D/'SOURCE_BINDING.json').read_text())
    for category,folder,count in [('cad_files','cad',157),('firmware_files','firmware',32)]:
        assert len(binding[category])==count
        for name,digest in binding[category].items():
            assert sha(W/'candidate'/folder/name)==digest,name
    assert binding['source_PCB_sha256']=='52ca35cf8cb4e2b4a27d053686ee3a85564f1e94dfdb7dcb4bca4083dd527312'
    regenerated=[D/'FINAL_REDLINE_VERIFICATION.json',D/'THERMAL_RESULTS.json',W/'product/PACKAGE_VERIFICATION.json']
    before={p:p.read_bytes() for p in regenerated}
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
    for name in ['finalize_redline.py','verify_package.py']:
        result=subprocess.run([sys.executable,str(D/name)],cwd=ROOT,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (a.out/(name+'.log')).write_text(result.stdout)
        print(result.stdout[-12000:],flush=True)
        assert result.returncode==0,name
    for path,data in before.items():
        assert path.read_bytes()==data,'Committed aggregate differs from reproduced result: '+str(path)
    final=json.loads((D/'FINAL_REDLINE_VERIFICATION.json').read_text())
    assert len(final['gates'])==14 and all(final['gates'].values())
    assert final['physical_tests']==0 and final['supplier_approval'] is False and final['manufacturing_order'] is False
    record={'status':'PASS_CURRENT_I32_EVIDENCE_AND_PACKAGE_REPRODUCTION',
            'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'source_PCB_sha256':binding['source_PCB_sha256'],'verified_changed_paths':len(inventory['files']),
            'native_CAD_inputs':157,'unchanged_firmware_files':32,'desktop_gates':14,
            'full_waveform_records':38,'aggregate_outputs_byte_identical':True,
            'physical_tests':0,'supplier_approval':False,'manufacturing_order':False}
    (a.out/'VERIFICATION.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))

if __name__=='__main__':
    main()
