#!/usr/bin/env python3
"""Preserve exact experiment records, including failed/rejected alternatives.

Full waveforms live in bounded-size archives. Compact decks/logs/results remain
in Git. An optional verified move avoids retaining two huge local copies.
"""
from pathlib import Path
import argparse, gzip, hashlib, json, shutil, zipfile, tempfile, os
D=Path(__file__).resolve().parent
SELECTED={'power_final_c166_68n','power_final_c166_68n_recovery','input_selected_final','input_controlled_final','input_unloaded_repeat'}
def remove_verified_duplicate(p):
    # Some synchronized workspaces can restore a removed large intermediate.
    # Record the empty replacement first; only call after retained-byte proof.
    p.write_bytes(b'');p.unlink()
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,a):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(a,indent=2)+'\n')
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--runs',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--move-raw-after-verify',action='store_true');ap.add_argument('--exclude-group',action='append',default=[],help='Running experiment groups; preserve them in a later invocation.');a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=True);root=a.runs.resolve();compact=D/'evidence';cases=sorted({p.parent for p in root.rglob('*.cir')if p.relative_to(root).parts[0]not in a.exclude_group})
    manifest=[];raws=[]
    for case in cases:
        rel=case.relative_to(root);group=rel.parts[0];selected=group in SELECTED
        scope='selected_model' if selected else 'historical_vendor_attempt' if group.startswith('vendor') else 'superseded_or_exploratory_not_selected'
        dest=compact/('runs' if selected or group.startswith('vendor') else 'rejected')/rel
        try:r=json.loads((case/'RESULT.json').read_text()) if (case/'RESULT.json').exists() else {}
        except json.JSONDecodeError:r={'status':'INCOMPLETE_OR_INVALID_RESULT_FILE_RETAINED'}
        record=dict(path=rel.as_posix(),scope=scope,completed=r.get('completed'),status=r.get('status'),parameters=r.get('parameters'),files={})
        for p in sorted(case.iterdir()):
            if not p.is_file() or p.name.startswith('.') or 'waveform' in p.name:continue
            if p.suffix.lower() not in ['.cir','.lib','.json','.log','.txt','.csv'] and p.name!='completion':continue
            # All exact decks, models, logs and result rows; selected/vendor plots.
            if p.suffix=='.csv' and not (selected or group.startswith('vendor')):continue
            data=p.read_bytes();name=p.name
            if p.suffix=='.csv':data=gzip.compress(data,compresslevel=6,mtime=0);name+='.gz'
            (dest/name).parent.mkdir(parents=True,exist_ok=True);(dest/name).write_bytes(data)
            record['files'][name]=dict(sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
        waveforms=sorted(p for p in case.iterdir() if p.is_file() and p.stat().st_size and not p.name.startswith('.') and 'waveform' in p.name and p.suffix in ['.tsv','.raw','.gz'])
        names={p.name for p in waveforms}
        for p in waveforms:
            if p.suffix=='.gz':continue
            target=p.with_name(p.name+'.gz')
            if not target.exists():
                with p.open('rb')as f,gzip.open(target,'wb',compresslevel=1)as z:shutil.copyfileobj(f,z)
            # Verify before dropping a raw duplicate; malformed prior gzip is
            # repaired from the complete raw bytes, never called a complete run.
            rawsha=digest(p)
            try:
                with gzip.open(target,'rb')as f:ok=hashlib.file_digest(f,'sha256').hexdigest()==rawsha
            except (EOFError,OSError):ok=False
            if not ok:
                tmp=target.with_suffix('.recovered')
                with p.open('rb')as f,gzip.open(tmp,'wb',compresslevel=1)as z:shutil.copyfileobj(f,z)
                with gzip.open(tmp,'rb')as f:assert hashlib.file_digest(f,'sha256').hexdigest()==rawsha
                target.write_bytes(tmp.read_bytes());tmp.unlink()
            if selected and r.get('completed') and p.name=='waveform.tsv':assert rawsha==r['waveform_sha256'],str(p)
            if a.move_raw_after_verify:remove_verified_duplicate(p)
        for p in sorted(case.glob('*waveform*.gz')):
            if p.name.startswith('.')or not p.stat().st_size:continue
            compressedsha=digest(p);rawsha=None
            if selected and r.get('completed'):
                with gzip.open(p,'rb')as f:rawsha=hashlib.file_digest(f,'sha256').hexdigest()
                assert rawsha==r['waveform_sha256'],str(p)
            raws.append(dict(path=p,member=p.relative_to(root).as_posix(),sha256=compressedsha,bytes=p.stat().st_size,full_record_sha256=rawsha,scope=scope))
        manifest.append(record)
    put(compact/'EXPERIMENT_INDEX.json',dict(cases=manifest,note='Only selected groups may support I32 numerical acceptance. Completion alone is not a pass. Full records are separately archived; missing/aborted records are not fabricated. Historical I31 61-case archive and newer 132-case summary remain separate.'))
    prior=a.out/'FULL_RECORD_ARCHIVES.json'
    archive_rows=json.loads(prior.read_text()) if prior.exists() else []
    already={q['member']:dict(q,archive=arc['file']) for arc in archive_rows for q in arc['records']}
    remaining=[]
    for row in raws:
        if row['member'] in already:
            old=already[row['member']]
            equal=row['sha256']==old['sha256']
            if not equal:
                try:
                    with gzip.open(row['path'],'rb')as f:newraw=hashlib.file_digest(f,'sha256').hexdigest()
                    with zipfile.ZipFile(a.out/old['archive'])as z,z.open(old['member'])as f,gzip.GzipFile(fileobj=f)as g:oldraw=hashlib.file_digest(g,'sha256').hexdigest()
                    equal=newraw==oldraw
                except (OSError,EOFError):equal=False
            if equal:
                if a.move_raw_after_verify:remove_verified_duplicate(row['path'])
            else:
                row['member']='retained_variants/'+row['sha256']+'/'+row['member'];row['scope']='alternate_raw_bytes_retained_not_promoted_to_selected';remaining.append(row)
        else:remaining.append(row)
    raws=remaining
    # Group selected first, then vendor attempts, then rejected alternatives.
    raws.sort(key=lambda r:({'selected_model':0,'historical_vendor_attempt':1}.get(r['scope'],2),r['member']))
    pending=[];size=0
    def finish(batch):
        if not batch:return
        number=len(archive_rows)+1;path=a.out/f'GR86_RevB_I32_Full_Records_{number:02d}.zip'
        assert not path.exists(),path
        rows=[{k:v for k,v in r.items()if k!='path'}for r in batch]
        fd,tmp=tempfile.mkstemp(prefix='gr86_i32_records_',suffix='.zip');os.close(fd);temporary=Path(tmp)
        with zipfile.ZipFile(temporary,'w',compression=zipfile.ZIP_STORED,allowZip64=True)as z:
            for row in batch:z.write(row['path'],row['member'])
            z.writestr('RECORD_MANIFEST.json',json.dumps(rows,indent=2)+'\n')
            z.writestr('README.md','# I32 full experiment records\n\nEach member is a lossless gzip record. The manifest preserves its original experiment path and exact compressed-byte SHA256. Selected records also verify the full uncompressed record against the completed simulation result. Rejected/historical scopes do not become selected-source passes. Exact decks/logs/results are in the companion I32 evidence tree and source commit.\n')
        with zipfile.ZipFile(temporary)as z:
            assert z.testzip() is None
            for row in batch:
                with z.open(row['member'])as f:assert hashlib.file_digest(f,'sha256').hexdigest()==row['sha256']
        # Publish the complete verified container atomically. Never expose an
        # actively growing ZIP to workspace synchronization.
        os.replace(temporary,path);os.utime(path,None)
        info=dict(file=path.name,bytes=path.stat().st_size,sha256=digest(path),records=rows)
        archive_rows.append(info);put(a.out/'FULL_RECORD_ARCHIVES.json',archive_rows)
        # A verified archive is now the retained exact copy. No sole record is deleted.
        if a.move_raw_after_verify:
            for row in batch:remove_verified_duplicate(row['path'])
        print(f'Preserved archive {number}: {len(batch)} records, {path.stat().st_size} bytes',flush=True)
    for row in raws:
        if pending and size+row['bytes']>350_000_000:finish(pending);pending=[];size=0
        pending.append(row);size+=row['bytes']
    finish(pending)
    put(D/'FULL_RECORD_ARCHIVES.json',archive_rows)
    print(json.dumps(dict(experiment_directories=len(cases),raw_records=len(raws),archives=len(archive_rows))),flush=True)
if __name__=='__main__':main()
