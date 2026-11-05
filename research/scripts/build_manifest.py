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
HANDOFF='2a40c7bb3af080981653f975b5c1e983e4f78ef5'

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
    patch_gate=load(ROOT/'research/audit/patch-integrity.json')
    tests=load(ROOT/'research/audit/test-inventory.json')
    receipts=load(D/'receipts/index.json')['receipts']
    blockers=load(D/'BLOCKERS.json')['blockers']
    manifest={
      'schema':'luma-audit-delivery/2',
      'base_sha':BASE,'handoff_sha':HANDOFF,'checkout_head_sha_at_generation':git('rev-parse','HEAD'),
      'implementation_commit_sha':args.implementation_commit,
      'commit_semantics':'implementation_commit_sha identifies the commit containing follow-up audit/tooling and the unapplied candidate; a subsequent manifest-recording commit may be HEAD.',
      'candidate_status':'GIT_INTEGRITY_VERIFIED_UNAPPLIED_NATIVE_BLOCKED',
      'native_source_unchanged':protection['native_source_unchanged'] and patch_gate['application_source_unchanged'],
      'protected_files_checked':protection['checked_files'],
      'physical_tv_commands':0,'physical_tv_evidence':'NOT_RUN',
      'handoff_integrity':{'all_match':integrity['all_match'],'files':integrity['file_count'],'report':'research/audit/handoff-integrity.json'},
      'patch_integrity':{'all_passed':patch_gate['all_passed'],'forward_apply':patch_gate['forward_apply'],'reverse_apply':patch_gate['reverse_apply'],'report':'research/audit/patch-integrity.json'},
      'native_test_inventory':{'static_attributes':tests['count'],'status':'NOT_RUN','blocker':'Rust/Cargo/SDL toolchain unavailable'},
      'test_results':[
        {'id':'baseline-node','exit':1,'passed':36,'total':37,'status':'FAIL_ENVIRONMENT','scope':'Historical named Node baseline; release case could not spawn pnpm'},
        {'id':'supported-node','exit':0,'passed':19,'total':19,'status':'PASS_HOST','scope':'Dependency-free companion suites only'},
        {'id':'release-node-supported','exit':0,'passed':17,'total':17,'status':'PASS_HOST','scope':'Supported release subset only'},
        {'id':'verify-offline','exit':1,'status':'BLOCKED_HISTORICAL','scope':'Previous handoff missing streamMetrics.mjs'},
        {'id':'verify-offline-updated','exit':0,'passed':11,'total':11,'status':'PASS_HOST','scope':'Updated handoff verifier; Python/JSON parses plus 11 Node assertions; native/TV NOT_RUN'},
        {'id':'patch-integrity-isolated','exit':0,'status':'PASS_SOURCE_INTEGRITY','scope':'Forward/reverse apply and three negative controls in external non-Git scratch'},
        {'id':'research-tests-final-corrected','exit':0,'passed':31,'total':31,'status':'PASS_HOST_SYNTHETIC','scope':'Python research/tooling contracts; no native rendering'},
        {'id':'build-environment-spec','exit':0,'status':'PASS_READ_ONLY_SPEC','scope':'Manual environment derivation; no installs/downloads/builds'},
        {'id':'native-preflight','exit':1,'status':'BLOCKED','scope':'Read-only native desktop preflight; required tools/inputs missing; no native tests'},
        {'id':'reference-tests','exit':1,'status':'FAIL_REAL_DEFECT','scope':'First comparison suite caught tip-relative blob counting; fixed by pinning to the audit base'},
        {'id':'reference-tests-corrected','exit':0,'passed':63,'total':63,'status':'PASS_HOST_SYNTHETIC','scope':'Python comparison math/facts plus existing research contracts; no native build, rendering or TV'},
        {'id':'cli-tests','exit':0,'passed':76,'total':76,'status':'PASS_HOST_SYNTHETIC','scope':'Adds luma_cli.py orientation/forensics/math coverage to the full Python suite; no native build, rendering or TV'},
        {'id':'native-regressions','exit':127,'status':'BLOCKED','scope':'cargo test unavailable'}
      ],
      'candidate_patch':{'path':'delivery/patches/focus-depth.patch','sha256':sha(D/'patches/focus-depth.patch'),'default':'OFF','enable':'LUMA_FOCUS_DEPTH=1','persistent_preference':False,'paths':['src/main.rs','src/view.rs','src/focus_experiment.rs'],'apply_verified':patch_gate['all_passed'] and patch_gate['forward_apply'],'reverse_apply_verified':patch_gate['all_passed'] and patch_gate['reverse_apply'],'native_tests':'NOT_RUN'},
      'build_environment':{'spec':'delivery/build-environment.json','guide':'delivery/BUILD-ENVIRONMENT.md','automatic_install':False},
      'native_validation':{'runbook':'delivery/NATIVE-VALIDATION.md','status_file':'delivery/native-validation-status.json','status':load(D/'native-validation-status.json')['status'],'native_tests_run':False},
      'reference_comparison':{'reference_repo':'funnymataleao/luma-webos-launcher','reference_commit':'40994fc144b5af481056d14e2fb93304aa1e2c82','reference_license':'MIT','compared_against':BASE,'report':'research/luma-audit/REFERENCE-LAUNCHER-COMPARISON.md','facts':'research/audit/reference-launcher-facts.json','doc_code_budgets_match':load(ROOT/'research/audit/reference-launcher-facts.json')['budgets']['match'],'independent_of_candidate':load(ROOT/'research/audit/reference-launcher-facts.json')['focus']['independent_of_our_experiment'],'imported_into_checkout':False,'native_or_visual_result':'NOT_RUN'},
      'dev_tooling':{'cli':'research/scripts/luma_cli.py','packet':'delivery/NEXT-AGENT-PACKET.md','commands':['map','docs','components','review','math','gates','forensics','status','test'],'installs_anything':False,'contacts_device':False,'note':'Thin wrapper over existing scripts/modules; protected_paths.py is the single source of truth build_audit.py also imports, replacing a hand-duplicated literal.'},
      'performance_proposals':'delivery/PERFORMANCE-PROPOSALS.md',
      'reference_provenance':{'report':'research/luma-audit/references.md','machine_readable':'research/audit/reference-provenance.json'},
      'open_blockers':[b['id'] for b in blockers if b['status']=='OPEN'],
      'resolved_blockers':[b['id'] for b in blockers if b['status']=='RESOLVED'],
      'receipts':receipts,'files':files,
      'evidence_policy':'OBSERVED source != MEASURED runtime. Host/synthetic/static results are not TV performance, GPU memory, native compilation or physical recovery evidence.'
    }
    (D/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'manifest':str(D/'manifest.json'),'files':len(files),'sha256':sha(D/'manifest.json')}))

if __name__=='__main__': main()
