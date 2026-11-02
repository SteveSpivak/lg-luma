#!/usr/bin/env python3
"""Sanitize already-collected immutable reference receipts; performs no network access."""
from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parents[2]
RAW=Path('/home/user/luma-research-evidence/references')
PINS={
 'SteveSpivak/webos-lens':'e5811544ec464666401e5306a420f5363076f88e',
 'NuvioMedia/NuvioTVSmart':'657c8a308d0c36aca1625a5e9293b3ba651f017b',
}
BUNDLED={
 'research/arena-handoff/offline-lab/cli/evidence_tools.py':'eded286e7fe860e400d8d186da65f6bab47fbccf',
 'research/arena-handoff/offline-lab/cli/correlate.py':'b460531d116fb9bbba95c93c33cebf2b47729757',
 'research/arena-handoff/references/lens-evidence.schema.json':'aa3867a1be2195fd9c2fda92786b0ffc6cb6e180',
}

def main():
    repos=[]
    for repo,sha in PINS.items():
        directory=RAW/repo.replace('/','__')/sha
        receipts=sorted(directory.glob('receipt-*.json'))
        selected=None
        for path in receipts:
            data=json.loads(path.read_text())
            if data.get('files'): selected=data; break
        if selected is None: raise SystemExit(f'Missing selected-file receipt: {repo}')
        repos.append({'repo':repo,'requested_sha':sha,'verified_commit':selected['verified_commit'],'tree_sha':selected['tree_sha'],
                      'collected_utc':selected['collected_utc'],'metadata_sha256':selected['metadata_sha256'],
                      'files':[{k:f[k] for k in ('path','git_blob_sha1','sha256','bytes')} for f in selected['files']]})
    bundled=[]
    for path,expected in BUNDLED.items():
        data=(ROOT/path).read_bytes()
        blob=hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()
        bundled.append({'path':path,'git_blob_sha1':blob,'sha256':hashlib.sha256(data).hexdigest(),'matches_verified_webos_lens_tree':blob==expected})
    out={'schema':'luma-reference-provenance/1','access_policy':'No network requests; summarizes prior verified collections only. Blocked repositories remain BLOCKED in references.md.',
         'verified_repositories':repos,'bundled_webos_lens_snapshot':bundled,
         'caveat':'Bundled snapshot integrity is separate from upstream origin proof. evidence_tools exporter agent SHA is checkout provenance, not lens origin.'}
    path=ROOT/'research/audit/reference-provenance.json'; path.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'path':str(path),'repos':len(repos),'bundled_matches':all(b['matches_verified_webos_lens_tree'] for b in bundled)}))
    if not all(b['matches_verified_webos_lens_tree'] for b in bundled): raise SystemExit(1)

if __name__=='__main__': main()
