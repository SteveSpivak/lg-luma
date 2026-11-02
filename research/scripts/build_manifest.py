#!/usr/bin/env python3
"""Build delivery manifest from verified artifacts. Never claims native/device PASS."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess

ROOT=Path(__file__).resolve().parents[2]
D=ROOT/'delivery'
BASE='e5608cd053be5376a54a806129a332952dfabcef'
HANDOFF='0aa7bd6ac099fc457179debbf749f0227c714158'

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path): return json.loads(path.read_text())
def git(*a): return subprocess.check_output(['git',*a],cwd=ROOT,text=True).strip()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--implementation-commit'); args=ap.parse_args()
    files={}
    for directory in ('delivery','research'):
        for path in sorted((ROOT/directory).rglob('*')):
            if not path.is_file() or path==D/'manifest.json' or '__pycache__' in path.parts: continue
            rel=str(path.relative_to(ROOT))
            files[rel]={'sha256':sha(path),'bytes':path.stat().st_size}
    protection=load(ROOT/'research/audit/source-protection.json')
    integrity=load(ROOT/'research/audit/handoff-integrity.json')
    tests=load(ROOT/'research/audit/test-inventory.json')
    receipts=load(D/'receipts/index.json')['receipts']
    blockers=load(D/'BLOCKERS.json')['blockers']
    manifest={
      'schema':'luma-audit-delivery/1',
      'base_sha':BASE,'handoff_sha':HANDOFF,'checkout_head_sha_at_generation':git('rev-parse','HEAD'),
      'implementation_commit_sha':args.implementation_commit,
      'commit_semantics':'implementation_commit_sha identifies the commit containing the unapplied candidate patch and audit; a subsequent manifest-recording commit may be HEAD.',
      'candidate_status':'PROPOSED_UNAPPLIED_NATIVE_BLOCKED',
      'native_source_unchanged':protection['native_source_unchanged'],
      'protected_files_checked':protection['checked_files'],
      'physical_tv_commands':0,'physical_tv_evidence':'NOT_RUN',
      'handoff_integrity':{'all_match':integrity['all_match'],'files':len(integrity['files']),'report':'research/audit/handoff-integrity.json'},
      'native_test_inventory':{'static_attributes':tests['count'],'status':'NOT_RUN','blocker':'Rust/Cargo/SDL toolchain unavailable'},
      'test_results':[
        {'id':'baseline-node','exit':1,'passed':36,'total':37,'status':'FAIL_ENVIRONMENT','scope':'Named Node baseline; release case could not spawn pnpm'},
        {'id':'supported-node','exit':0,'passed':19,'total':19,'status':'PASS_HOST','scope':'Dependency-free companion suites only'},
        {'id':'release-node-supported','exit':0,'passed':17,'total':17,'status':'PASS_HOST','scope':'Supported release subset only'},
        {'id':'verify-offline','exit':1,'status':'BLOCKED','scope':'Python/JSON parse passed; Node stats import missing streamMetrics.mjs'},
        {'id':'offline-evidence-and-metrics-corrected','exit':0,'passed':16,'total':16,'status':'PASS_HOST_SYNTHETIC','scope':'Unchanged bundled evidence processor + independent arithmetic/static contracts'},
        {'id':'candidate-static-contract','exit':0,'passed':1,'total':1,'status':'PASS_STATIC','scope':'Bounded/default-off patch text only'},
        {'id':'candidate-apply-check','exit':1,'status':'FAIL_STOPPED','scope':'Missing new-file mode header; generator corrected, apply not rechecked after two failures'},
        {'id':'native-regressions','exit':127,'status':'BLOCKED','scope':'cargo test unavailable'}
      ],
      'candidate_patch':{'path':'delivery/patches/focus-depth.patch','sha256':sha(D/'patches/focus-depth.patch'),'default':'OFF','enable':'LUMA_FOCUS_DEPTH=1','persistent_preference':False,'paths':['src/main.rs','src/view.rs','src/focus_experiment.rs'],'apply_verified':False,'native_tests':'NOT_RUN'},
      'reference_provenance':{'report':'research/luma-audit/references.md','machine_readable':'research/audit/reference-provenance.json'},
      'blockers':[b['id'] for b in blockers],
      'receipts':receipts,'files':files,
      'evidence_policy':'OBSERVED source != MEASURED runtime. Host/synthetic/static results are not TV performance, GPU memory, native compilation or physical recovery evidence.'
    }
    (D/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'manifest':str(D/'manifest.json'),'files':len(files),'sha256':sha(D/'manifest.json')}))

if __name__=='__main__': main()
