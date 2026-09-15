#!/usr/bin/env python3
"""Verify or restore lossless gzip waveforms stored in exact byte parts."""
from pathlib import Path
import argparse, gzip, hashlib, json, os, tempfile

D = Path(__file__).resolve().parent / 'spice'

def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def verify_parts(record, restore=False):
    target = D / record['waveform_gz']
    parts = record.get('byte_parts')
    if not parts:
        assert sha(target) == record['compressed_sha256']
        return
    # Reconstruct into a temporary sibling, verify the compressed and full raw
    # streams, then optionally install. Never overwrite a differing local file.
    fd, name = tempfile.mkstemp(prefix='.record-verify-', dir=target.parent)
    temp = Path(name)
    try:
        with os.fdopen(fd, 'wb') as out:
            for part in parts:
                p = D / part['path']
                assert p.stat().st_size == part['bytes'] and sha(p) == part['sha256']
                with p.open('rb') as inp:
                    for block in iter(lambda: inp.read(4 * 1024 * 1024), b''):
                        out.write(block)
        assert sha(temp) == record['compressed_sha256']
        with gzip.open(temp, 'rb') as inp:
            assert hashlib.file_digest(inp, 'sha256').hexdigest() == record['uncompressed_sha256']
        if target.exists():
            assert sha(target) == record['compressed_sha256'], 'Different existing record: ' + str(target)
        elif restore:
            temp.rename(target)
    finally:
        if temp.exists():
            temp.unlink()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--restore', action='store_true', help='Install verified reconstructed gzip files.')
    args = parser.parse_args()
    manifest = json.loads((D / 'RAW_RECORD_MANIFEST.json').read_text())
    for record in manifest['records']:
        verify_parts(record, args.restore)
    print(f"PASS: {len(manifest['records'])} raw payloads preserved; {sum(bool(r.get('byte_parts')) for r in manifest['records'])} split gzip streams verified byte-for-byte and after decompression.")

if __name__ == '__main__':
    main()
