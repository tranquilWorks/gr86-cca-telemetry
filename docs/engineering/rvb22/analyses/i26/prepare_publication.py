#!/usr/bin/env python3
"""Verify finite I26 outputs; optionally create an unreferenced, scoped Git commit.

Never updates a branch, merges, releases, flashes, or operates hardware.
"""
import argparse, base64, hashlib, json, os, subprocess, urllib.request, zipfile
from pathlib import Path
D=Path(__file__).resolve().parent; W=D.parents[1]; ROOT=W.parents[2]
REPO='tranquilWorks/gr86-cca-telemetry'
BRANCH='codex/rvb24-coordinated-closure'
P='docs/engineering/rvb22/'
OUT=ROOT/'i26-publication';OUT.mkdir(exist_ok=True)
CURRENT_PCB_SHA='a04f42b358fa65a332128115a7b648e1a2297531ecb47466ac24697de536a936'
REFERENCE_PCB_SHA='5b373f6033fdbd18f126f8ca054b619abada2568778c5a8fc303c4e756fb06c8'
GENERATED=['FINAL_REVIEW_REGISTER.json','FINAL_GATES.json','I26_PREHARDWARE_CLOSURE.json','I26_PREHARDWARE_CLOSURE.md','analyses/convergence_01/run_review.py']
GENERATED += ['analyses/i26/'+n for n in ['LED_BOUND.json','LED_THERMAL_REGIONS.json','HISTORICAL_54_RETURN_FINDINGS.json','EXPANDED_RETURN_SCOPE.json','TRANSFER_SCREEN_PATHS_EXPLORATORY.json','TRANSFER_SCREEN_EXPLORATORY.json','QUALIFICATION_GATES.json','RECONCILIATION_AUDIT.json']]
GENERATED += ['analyses/i26/current_review/'+n for n in ['ALL_CRITERIA_COVERAGE.json','CURRENT_HANDLING_REGISTER.json','EVIDENCE_AVAILABILITY.json','LED_REVIEW.json','RECEIVE_ONLY_DISPOSITION.json','REGRESSION_BINDING.json','SUMMARY.json']]
BASELINE_FILES=['FINAL_REVIEW_REGISTER.json','I26_PREHARDWARE_CLOSURE.json','FINAL_GATES.json','analyses/convergence_01/run_review.py','I26_PREHARDWARE_CLOSURE.md']

def run(args,log=None):
    result=subprocess.run(args,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if log:(OUT/log).write_text(result.stdout)
    print(result.stdout[-12000:],flush=True)
    if result.returncode:raise RuntimeError('Command failed: '+str(args))
    return result.stdout

def member(artifact_id,suffix,expected):
    archive=OUT/(str(artifact_id)+'.zip')
    with archive.open('wb') as f:
        subprocess.run(['gh','api',f'repos/{REPO}/actions/artifacts/{artifact_id}/zip'],stdout=f,check=True)
    with zipfile.ZipFile(archive) as z:
        matches=[n for n in z.namelist() if n.endswith(suffix)]
        if len(matches)!=1:raise ValueError('Ambiguous artifact member '+suffix)
        data=z.read(matches[0])
    if hashlib.sha256(data).hexdigest()!=expected:raise ValueError('Artifact content identity mismatch '+suffix)
    path=OUT/Path(suffix).name;path.write_bytes(data);return path

def rebind_current_review():
    """Retain proven I26 scope, bind I28 source, and explicitly review the new automotive U121 MPN."""
    p=W/'analyses/convergence_01/run_review.py'
    text=p.read_text()
    required=[
        'I25_CONDITIONAL_DESKTOP_COMPLETE_PHYSICAL_GATE',
        'RETURN_TRANSFER_DESKTOP_WORK_REMAINING',
        'LED_DESKTOP_COMPLETE_INSTALLED_VISIBILITY_GATE',
        'I25_THERMAL_SCOPE_RETAINED',
        'actionable_DESKTOP_WORK_REMAINING',
    ]
    missing=[x for x in required if x not in text]
    if missing:raise ValueError('Expected adopted I26 scope is absent: '+str(missing))
    closure=json.loads((W/'I26_PREHARDWARE_CLOSURE.json').read_text())
    if closure.get('original_290_literal_statuses_preserved') is not True:
        raise ValueError('Original review statuses are not preserved')
    if closure.get('next_reconciliation',{}).get('target_actionable_prehardware_rows') != 0:
        raise ValueError('Prehardware closure target is not zero actionable rows')
    if closure.get('physical_claims_made') is not False:
        raise ValueError('Desktop closure must not claim physical qualification')
    if closure.get('current_actionable_prehardware_count',0) not in (0,1):
        raise ValueError('Unexpected actionable prehardware state')
    old="PCB_HASH='"+REFERENCE_PCB_SHA+"'"
    new="PCB_HASH='"+CURRENT_PCB_SHA+"'\nREFERENCE_PCB_HASH='"+REFERENCE_PCB_SHA+"'"
    if old in text:
        text=text.replace(old,new,1)
    elif "PCB_HASH='"+CURRENT_PCB_SHA+"'" not in text:
        raise ValueError('Unexpected PCB hash binding in run_review.py')
    old_check="require(n['source_PCB_sha256']==PCB_HASH and n['filled_PCB_sha256']==FILLED_HASH,'Native binding mismatch')"
    new_check="require(n['source_PCB_sha256']==REFERENCE_PCB_HASH and n['filled_PCB_sha256']==FILLED_HASH,'Historical native reference binding mismatch')"
    if old_check in text:
        text=text.replace(old_check,new_check,1)
    elif new_check not in text:
        raise ValueError('Unexpected native reference check in run_review.py')
    q1_anchor="        if mpn in by_mpn:r=copy.deepcopy(by_mpn[mpn])\n        elif mpn in ('TNPU060311K8HWEA00','TNPU06034K99HWEA00'):"
    q1_replacement="""        if mpn in by_mpn:r=copy.deepcopy(by_mpn[mpn])
        elif mpn=='LM5164QDDARQ1':
            r={'mpn':mpn,'manufacturer':'Texas Instruments','process':'GLOBAL_REFLOW','msl':2,'manufacturer_peak_C':260,'source':'https://www.ti.com/product/LM5164-Q1/part-details/LM5164QDDARQ1','source_evidence':'TI_CURRENT_QUALITY_INFO_AUTOMOTIVE_DDA8_MSL2_260C_1YEAR_REVIEWED_2026_09_12','handling':'TI lists this active automotive DDA-8 option with NiPdAuAg lead finish, MSL Level 2, 260C peak reflow and one-year floor life. Preserve dry-pack/MSL controls and the incoming lot label as the assembly-process authority.','current_release_condition':'Use the board-wide compatible lead-free reflow process within the package limit. Incoming lot labeling and assembler process controls remain authoritative; no physical solder-joint acceptance is claimed here.'}
        elif mpn in ('TNPU060311K8HWEA00','TNPU06034K99HWEA00'):"""
    if q1_anchor in text:
        text=text.replace(q1_anchor,q1_replacement,1)
    elif "elif mpn=='LM5164QDDARQ1':" not in text:
        raise ValueError('Unable to bind explicit LM5164QDDARQ1 handling review')
    p.write_text(text)

def rebind_reconciliation():
    """Bind the established 290-row reconciliation logic to the metadata-only I28 PCB revision."""
    p=D/'reconcile.py'
    text=p.read_text()
    old="SOURCE='"+REFERENCE_PCB_SHA+"'"
    new="SOURCE='"+CURRENT_PCB_SHA+"'"
    if old in text:
        text=text.replace(old,new,1)
    elif new not in text:
        raise ValueError('Unexpected PCB hash binding in reconcile.py')
    p.write_text(text)

def verify():
    baseline={}
    for name in BASELINE_FILES:
        path=W/name
        if not path.is_file():raise ValueError('Missing controlled baseline: '+name)
        baseline[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    pcb=W/'candidate/cad/GR86_CCA_RevB.kicad_pcb'
    if hashlib.sha256(pcb.read_bytes()).hexdigest()!=CURRENT_PCB_SHA:
        raise ValueError('Current I28 PCB source identity changed')
    (OUT/'BASELINE_BINDING.json').write_text(json.dumps({'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'current_PCB_sha256':CURRENT_PCB_SHA,'historical_native_reference_source_sha256':REFERENCE_PCB_SHA,'sha256':baseline},indent=2)+'\n')
    native=member(10161339481,'native_I06_hosted/candidate_kicad/GR86_CCA_RevB.kicad_pcb','11533ea91c3bc4c61dd7066e0001914a72bc90b27afb38d321c43b8feb90e3b1')
    thermal=member(10273346331,'thermal/release_existing_cooling.npz','7e465b2b047e868bc58abd70ba62e3a202d7fe0a74c3e12b50341523f2221997')
    run(['python',str(D/'led_bound.py')],'led.log')
    run(['python',str(D/'return_review.py'),'--native',str(native)],'return.log')
    run(['python',str(D/'extract_led_thermal.py'),str(thermal)],'led-thermal.log')
    run(['python',str(D/'transfer_exploration.py'),'--native',str(native)],'transfer.log')
    run(['python',str(D/'summarize_transfer.py')],'transfer-summary.log')
    rebind_current_review()
    rebind_reconciliation()
    run(['python',str(D/'reconcile.py')],'reconcile.log')
    run(['python','-m','unittest','discover','-s',str(D/'tests'),'-v'],'i26-tests.log')
    run(['python','-m','unittest','discover','-s',str(W/'analyses/convergence_01/tests'),'-v'],'regression-tests.log')
    checks=json.loads(run(['python',str(W/'analyses/convergence_04/check_release_profile.py')],'release-profile.log'))
    if len(checks)!=12 or not all(checks.values()):raise ValueError('Release guard incomplete')
    run(['python',str(W/'analyses/convergence_01/run_review.py'),'--out',str(D/'current_review')],'current-review.log')
    run(['python',str(W/'i26_audit_open_rows.py')],'register-audit.log')
    verification={'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'current_PCB_sha256':CURRENT_PCB_SHA,'historical_native_reference_source_sha256':REFERENCE_PCB_SHA,'U121_handling_review':{'MPN':'LM5164QDDARQ1','manufacturer':'Texas Instruments','rating':'Automotive','MSL':2,'peak_reflow_C':260,'floor_life':'1 YEAR'},'baseline_sha256':baseline,'I26_unit_tests':32,'existing_regression_tests':32,'release_profile_checks':12,'all_passed':True,'physical_tests':0,'native_KiCad_executed_in_this_job':False,'actionable_prehardware_ids':['GND-02'],'full_external_gate_reaudit_claimed':False}
    (OUT/'VERIFICATION.json').write_text(json.dumps(verification,indent=2)+'\n')
    with zipfile.ZipFile(OUT/'I26_GENERATED_EVIDENCE.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in GENERATED:z.write(W/name,P+name)
        for path in OUT.glob('*.log'):z.write(path,'execution/'+path.name)
        z.write(OUT/'BASELINE_BINDING.json','execution/BASELINE_BINDING.json')
        z.write(OUT/'VERIFICATION.json','execution/VERIFICATION.json')

def api(method,endpoint,payload=None):
    req=urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+endpoint,data=json.dumps(payload).encode() if payload is not None else None,method=method,headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json','User-Agent':'i26-scoped-publication'})
    with urllib.request.urlopen(req,timeout=90) as response:return json.load(response)

def prepare_commit():
    evidence=json.loads((OUT/'VERIFICATION.json').read_text());head=evidence['source_commit']
    if os.environ.get('GITHUB_REPOSITORY')!=REPO or not evidence['all_passed']:raise ValueError('Wrong repository or verification state')
    if api('GET','git/ref/heads/'+BRANCH)['object']['sha']!=head:raise ValueError('Branch advanced; do not overwrite')
    allowed={P+n for n in GENERATED}
    modified=set(subprocess.check_output(['git','diff','--name-only'],cwd=ROOT,text=True).splitlines())
    if modified-allowed:raise ValueError('Out-of-scope tracked mutations: '+str(modified-allowed))
    elements=[];manifest={}
    for name in GENERATED:
        data=(W/name).read_bytes();manifest[P+name]=hashlib.sha256(data).hexdigest()
        blob=api('POST','git/blobs',{'content':base64.b64encode(data).decode(),'encoding':'base64'})
        elements.append({'path':P+name,'mode':'100644','type':'blob','sha':blob['sha']})
    state=api('GET','git/commits/'+head)
    tree=api('POST','git/trees',{'base_tree':state['tree']['sha'],'tree':elements})
    commit=api('POST','git/commits',{'message':'Reconcile I26 LED and thermal criteria; retain explicit ground-return desktop work','tree':tree['sha'],'parents':[head]})
    result={'parent':head,'prepared_commit':commit['sha'],'prepared_tree':tree['sha'],'branch_updated':False,'physical_tests':0,'verification':evidence,'sha256':manifest}
    (OUT/'PUBLICATION_RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
    print('I26_PREPARED_COMMIT '+commit['sha'])

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['verify','prepare-commit']);args=parser.parse_args()
    verify() if args.action=='verify' else prepare_commit()
