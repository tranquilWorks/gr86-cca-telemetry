#!/usr/bin/env python3
"""Split/restore exact record ZIPs with per-part and whole-archive SHA256 checks."""
from pathlib import Path
import argparse,hashlib,json,os,tempfile,zipfile
CHUNK=350_000_000
def sha(p):
    with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def publish_temp(tmp,path):
    path.parent.mkdir(parents=True,exist_ok=True);os.replace(tmp,path);os.utime(path,None)
def split(folder,manifest,remove_originals=False):
    rows=json.loads(manifest.read_text());distribution=[]
    checkpoint=folder/'RAW_ARCHIVE_DISTRIBUTION.json'
    prior={r['archive']:r for r in json.loads(checkpoint.read_text())['archives']} if checkpoint.exists() else {}
    for archive in rows:
        path=folder/archive['file']
        if archive['file'] in prior:
            done=prior[archive['file']];combined=hashlib.sha256()
            assert done['archive_sha256']==archive['sha256'] and done['archive_bytes']==archive['bytes']
            for item in done['parts']:
                part=folder/item['file'];assert part.stat().st_size==item['bytes'] and sha(part)==item['sha256']
                with part.open('rb')as f:
                    while block:=f.read(8*1024*1024):combined.update(block)
            assert combined.hexdigest()==archive['sha256']
            if remove_originals and len(done['parts'])>1 and path.exists():path.write_bytes(b'')
            distribution.append(done);continue
        assert path.stat().st_size==archive['bytes']and sha(path)==archive['sha256'],path
        parts=[]
        if archive['bytes']<=CHUNK:
            parts=[dict(file=path.name,bytes=archive['bytes'],sha256=archive['sha256'])]
        else:
            with path.open('rb')as source:
                number=1
                while block:=source.read(CHUNK):
                    target=folder/(path.name+f'.part{number:02d}')
                    fd,tmp=tempfile.mkstemp(prefix='gr86_i32_part_');os.close(fd);tmp=Path(tmp);tmp.write_bytes(block);publish_temp(tmp,target)
                    digest=hashlib.sha256(block).hexdigest();assert sha(target)==digest
                    parts.append(dict(file=target.name,bytes=len(block),sha256=digest));number+=1
            combined=hashlib.sha256()
            for item in parts:
                with (folder/item['file']).open('rb')as f:
                    while block:=f.read(8*1024*1024):combined.update(block)
            assert combined.hexdigest()==archive['sha256']
            if remove_originals:path.write_bytes(b'')
        distribution.append(dict(archive=archive['file'],archive_bytes=archive['bytes'],archive_sha256=archive['sha256'],parts=parts,all_parts_and_concatenated_archive_verified=True))
        (folder/'RAW_ARCHIVE_DISTRIBUTION.json').write_text(json.dumps(dict(archives=distribution,complete=len(distribution)==len(rows)),indent=2)+'\n')
    return distribution
def restore(manifest,parts,output):
    data=json.loads(manifest.read_text());assert data['complete'];output.mkdir(parents=True,exist_ok=True)
    for item in data['archives']:
        target=output/item['archive'];assert Path(item['archive']).name==item['archive']
        if target.exists():assert target.stat().st_size==item['archive_bytes']and sha(target)==item['archive_sha256'];continue
        fd,tmp=tempfile.mkstemp(prefix='gr86_i32_restore_');os.close(fd);tmp=Path(tmp);combined=hashlib.sha256()
        with tmp.open('wb')as sink:
            for p in item['parts']:
                assert Path(p['file']).name==p['file'];source=parts/p['file'];assert source.stat().st_size==p['bytes']and sha(source)==p['sha256'],source
                with source.open('rb')as f:
                    while block:=f.read(8*1024*1024):sink.write(block);combined.update(block)
        assert tmp.stat().st_size==item['archive_bytes']and combined.hexdigest()==item['archive_sha256']
        with zipfile.ZipFile(tmp)as z:assert z.testzip()is None
        publish_temp(tmp,target);print(target.name,'verified')
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['split','restore']);ap.add_argument('--manifest',type=Path,required=True);ap.add_argument('--parts-dir',type=Path,required=True);ap.add_argument('--output-dir',type=Path);ap.add_argument('--remove-verified-originals',action='store_true');a=ap.parse_args()
    if a.action=='split':split(a.parts_dir,a.manifest,a.remove_verified_originals)
    else:
        assert a.output_dir is not None;restore(a.manifest,a.parts_dir,a.output_dir)
