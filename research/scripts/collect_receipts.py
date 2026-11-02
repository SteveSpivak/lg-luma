#!/usr/bin/env python3
"""Compact external raw receipts into sanitized, hash-linked delivery evidence."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[2]
RAW = Path("/home/user/luma-research-evidence/20261102")
OUT = ROOT / "delivery/receipts"
LABELS = {
 "baseline-git":("OBSERVED","Checkout/remote base identity only."),
 "toolchain":("OBSERVED","Availability probe; absent native tools are BLOCKED, not PASS."),
 "baseline-node":("MEASURED_HOST","Host test run only; pnpm-dependent release case failed."),
 "pnpm-test":("BLOCKED","Command unavailable; no test bodies ran."),
 "pnpm-check":("BLOCKED","Command unavailable; no test bodies ran."),
 "pnpm-format-check":("BLOCKED","Command unavailable; no formatting check ran."),
 "cargo-test":("BLOCKED","Command unavailable; no Rust compilation/tests ran."),
 "supported-node":("MEASURED_HOST","Dependency-free companion suites only; not full pnpm test."),
 "release-node-supported":("MEASURED_HOST","Supported release subset only; not full baseline."),
 "missing-pnpm-cause":("OBSERVED","Diagnostic reproduced child pnpm ENOENT; not a repaired baseline."),
 "handoff-pin-local":("OBSERVED","Local remote-tracking ref resolves to the previously verified exact handoff SHA; no refetch."),
 "handoff-integrity":("OBSERVED","All extracted handoff blobs compared with pinned Git tree."),
 "verify-offline":("BLOCKED","Verifier ran once; Python/JSON passed, Node import failed before assertions."),
 "candidate-static-red":("OBSERVED","Intentional red contract before candidate generation."),
 "candidate-apply-check":("FAIL","First apply check failed on missing new-file mode header; not native validation."),
 "research-tests-green":("FAIL","Combined suite: 17 passed, same candidate apply failure; retry loop stopped."),
 "build-audit":("FAIL","First inventory generator lacked output directory; corrected separately."),
 "build-audit-corrected":("OBSERVED","Pinned source/test inventory and protection checks; no native execution."),
 "offline-evidence-and-metrics":("FAIL","Initial synthetic suite exposed one wrong hand-computed arithmetic expectation."),
 "offline-evidence-and-metrics-corrected":("MEASURED_HOST","16 synthetic evidence/arithmetic tests passed; no device or native rendering."),
 "candidate-static-contract":("OBSERVED","Bounded/default-off patch text contract only; apply check not repeated."),
 "protected-source-diff":("OBSERVED","Native/protected paths unchanged against base."),
}

def redact(value):
    if isinstance(value,str):
        value=value.replace(str(ROOT),"<CHECKOUT>").replace("/home/user/luma-research-evidence","<EVIDENCE>")
        return re.sub(r"/home/user/[^\s\"']+", "<LOCAL_PATH>", value)
    if isinstance(value,list): return [redact(v) for v in value]
    if isinstance(value,dict): return {k:redact(v) for k,v in value.items()}
    return value

RAW_NAMES={"pnpm-test":"gate-pnpm_test","pnpm-check":"gate-pnpm_check","pnpm-format-check":"gate-pnpm_format_check","cargo-test":"gate-cargo_test_--locked_--workspace_--all-features"}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    index=[]
    for label,(evidence_class,caveat) in LABELS.items():
        path=RAW/f"{RAW_NAMES.get(label,label)}.json"
        if not path.exists():
            index.append({"label":label,"status":"MISSING_RAW_RECEIPT"})
            continue
        raw=json.loads(path.read_text())
        compact={"schema":"luma-sanitized-receipt/1","label":label,"evidence_class":evidence_class,"caveat":caveat,
                 "command_argv":redact(raw.get("command",[])),"exit_code":raw.get("exit_code"),"status":raw.get("status"),
                 "started_utc":raw.get("started_utc"),"duration_ms":raw.get("duration_ms"),
                 "stdout_sha256":raw.get("stdout_sha256"),"stdout_bytes":raw.get("stdout_bytes"),
                 "stderr_sha256":raw.get("stderr_sha256"),"stderr_bytes":raw.get("stderr_bytes"),
                 "head_sha":raw.get("head_sha"),"raw_receipt_sha256":__import__("hashlib").sha256(path.read_bytes()).hexdigest()}
        (OUT/f"{label}.json").write_text(json.dumps(compact,indent=2)+"\n")
        index.append({"label":label,"path":f"receipts/{label}.json","exit_code":raw.get("exit_code"),"status":raw.get("status"),"evidence_class":evidence_class})
    (OUT/"index.json").write_text(json.dumps({"schema":"luma-receipt-index/1","receipts":index},indent=2)+"\n")
    print(json.dumps({"receipts":len(index),"missing":[r['label'] for r in index if r['status']=='MISSING_RAW_RECEIPT']}))

if __name__=='__main__': main()
