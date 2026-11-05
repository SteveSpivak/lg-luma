#!/usr/bin/env python3
"""Compact external raw receipts into sanitized, hash-linked delivery evidence.

Reads receipt.py schema luma-command-receipt/1 (argv/head/outputs), never reruns
commands, and never copies raw logs into Git. Historical receipts are backfilled
from their original raw files so earlier null provenance fields are corrected.
"""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[2]
RAW_DIRS = (Path("/home/user/luma-research-evidence/20261105"), Path("/home/user/luma-research-evidence/20261102"))
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
 "handoff-pin-local":("OBSERVED","Previous handoff pin; retained as history."),
 "verify-offline":("BLOCKED","Previous verifier run; missing streamMetrics.mjs. Historical only."),
 "candidate-static-red":("OBSERVED","Intentional red contract before candidate generation."),
 "candidate-apply-check":("FAIL","Historical apply failure: missing new-file mode header; exact failed bytes were not retained."),
 "research-tests-green":("FAIL","Historical combined suite: 17 passed, same candidate apply failure."),
 "build-audit":("FAIL","First inventory generator lacked output directory; corrected separately."),
 "build-audit-corrected":("OBSERVED","Pinned source/test inventory and protection checks; no native execution."),
 "offline-evidence-and-metrics":("FAIL","Initial synthetic suite exposed one wrong hand-computed arithmetic expectation."),
 "offline-evidence-and-metrics-corrected":("MEASURED_HOST","16 synthetic evidence/arithmetic tests passed; no device or native rendering."),
 "candidate-static-contract":("OBSERVED","Bounded/default-off patch text contract only."),
 "protected-source-diff":("OBSERVED","Native/protected paths unchanged against base."),
 "handoff-update-fetch":("OBSERVED","Fetched requested updated handoff ref; no merge or checkout."),
 "handoff-update-integrity":("OBSERVED","18/18 files match updated pinned handoff; no extras."),
 "verify-offline-updated":("MEASURED_HOST","Updated verifier exited 0; 11/11 Node assertions and Python/JSON parses passed. Native/TV NOT_RUN."),
 "patch-integrity-gate":("FAIL","Harness rejected a tar directory member before any apply command ran."),
 "patch-integrity-gate-corrected":("FAIL","Harness exposed ignored .build scratch: reverse check was a no-op. No patch applicability claim."),
 "patch-integrity-isolated":("OBSERVED","External non-Git scratch: forward/reverse and three negative controls passed; source hashes unchanged. Not native validation."),
 "research-tests-followup":("MEASURED_HOST","Python research/tooling contracts only; native Rust/SDL and TV NOT_RUN."),
 "build-environment-spec":("OBSERVED","Read-only derivation from repository locks/CI; no installs, downloads, builds or device commands."),
 "research-tests-final":("MEASURED_HOST","Final Python research/tooling contracts only; native Rust/SDL and TV NOT_RUN."),
 "research-tests-final-corrected":("MEASURED_HOST","Corrected UNKNOWN-result schema consistency; Python contracts only; native/TV NOT_RUN."),
 "protected-source-diff-followup":("OBSERVED","Native/protected paths unchanged against base after follow-up research/tooling edits."),
 "remote-branch-check":("OBSERVED","Dedicated remote branch was absent before authorized push."),
 "dedicated-branch-push":("OBSERVED","Pushed only arena/0bee657b-lg-luma; no main push or merge."),
 "remote-branch-verify":("OBSERVED","Remote dedicated branch SHA verified after push."),
 "native-preflight":("BLOCKED","Read-only native desktop preflight; required tools/inputs missing. No installs or native tests."),
 "dedicated-branch-push-final":("OBSERVED","Pushed only dedicated branch after native-validation prep; no main push or merge."),
 "remote-branch-verify-final":("OBSERVED","Final remote dedicated branch SHA verified after prep push."),
 "reference-forensics":("OBSERVED","Pinned upstream fork compared read-only outside the checkout; file/constant counts only, nothing imported."),
 "reference-tests":("MEASURED_HOST","Python contracts for comparison arithmetic and recorded facts; no native build, rendering or TV."),
 "protected-source-diff-reference":("OBSERVED","Native/protected paths unchanged after the reference comparison."),
 "branch-history-recovery":("OBSERVED","Local clone was re-created at base by the environment; branch history restored from origin before new work."),
 "branch-history-recovery-2":("OBSERVED","A second, independent sandbox reset of local git history during the same session; restored from origin again before any commit."),
 "cli-dev-tests":("MEASURED_HOST","Full Python research/tooling suite including new luma_cli.py coverage; no native build, rendering or TV."),
 "cli-protected-source-diff":("OBSERVED","Native/protected paths unchanged after adding the CLI, packet and protected_paths.py extraction."),
 "reference-forensics-corrected":("OBSERVED","Corrected run: blob comparison pinned to the audit base instead of the moving branch tip. Read-only, nothing imported."),
 "reference-tests-corrected":("MEASURED_HOST","Preserved first failure was a real defect (tip-relative blobs); after pinning to the base, all Python contracts pass. No native/TV."),
}
RAW_NAMES={"pnpm-test":"gate-pnpm_test","pnpm-check":"gate-pnpm_check","pnpm-format-check":"gate-pnpm_format_check","cargo-test":"gate-cargo_test_--locked_--workspace_--all-features"}


def redact(value):
    if isinstance(value,str):
        value=value.replace(str(ROOT),"<CHECKOUT>").replace("/home/user/luma-research-evidence","<EVIDENCE>").replace("/home/user/luma-patch-integrity","<SCRATCH>")
        return re.sub(r"/home/user/[^\s\"']+", "<LOCAL_PATH>", value)
    if isinstance(value,list): return [redact(v) for v in value]
    if isinstance(value,dict): return {k:redact(v) for k,v in value.items()}
    return value


def compact_receipt(raw, label, evidence_class, caveat, raw_sha256):
    """Map the actual runner schema; do not silently substitute missing fields."""
    if raw.get("schema") != "luma-command-receipt/1":
        raise ValueError(f"Unsupported receipt schema for {label}")
    outputs=raw["outputs"]
    runner_label=raw["label"]
    stdout=outputs[f"{runner_label}.stdout.log"]
    stderr=outputs[f"{runner_label}.stderr.log"]
    return {"schema":"luma-sanitized-receipt/2","label":label,"evidence_class":evidence_class,"caveat":caveat,
            "command_argv":redact(raw["argv"]),"exit_code":raw["exit_code"],"status":raw["execution_status"],
            "started_utc":raw["started_utc"],"finished_utc":raw["finished_utc"],
            "duration_ms":round(raw["duration_seconds"]*1000,6),"timed_out":raw["timed_out"],
            "stdout_sha256":stdout["sha256"],"stdout_bytes":stdout["bytes"],
            "stderr_sha256":stderr["sha256"],"stderr_bytes":stderr["bytes"],
            "head_sha":raw["head"],"raw_receipt_sha256":raw_sha256,
            "evidence_scope":raw["evidence_scope"]}


def find_raw(name):
    for directory in RAW_DIRS:
        path = directory / f"{name}.json"
        if path.exists():
            return path
    return None


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    index = []
    missing = []
    for label, (evidence_class, caveat) in LABELS.items():
        path = find_raw(RAW_NAMES.get(label, label))
        committed = OUT / f"{label}.json"
        if path is not None:
            raw_bytes = path.read_bytes()
            raw = json.loads(raw_bytes)
            compact = compact_receipt(raw, label, evidence_class, caveat, hashlib.sha256(raw_bytes).hexdigest())
            committed.write_text(json.dumps(compact, indent=2) + "\n")
            index.append({"label": label, "path": f"receipts/{label}.json", "exit_code": raw["exit_code"],
                          "status": raw["execution_status"], "evidence_class": evidence_class, "source": "raw"})
        elif committed.exists():
            # The raw log is gone (environment reset). Keep the previously committed,
            # hash-linked receipt as history; never re-derive or re-run it here.
            existing = json.loads(committed.read_text())
            index.append({"label": label, "path": f"receipts/{label}.json", "exit_code": existing["exit_code"],
                          "status": existing["status"], "evidence_class": existing["evidence_class"],
                          "source": "committed_historical"})
        else:
            index.append({"label": label, "status": "MISSING_RAW_RECEIPT"})
            missing.append(label)
    (OUT / "index.json").write_text(json.dumps({"schema": "luma-receipt-index/1", "receipts": index}, indent=2) + "\n")
    print(json.dumps({"receipts": len(index), "from_raw": sum(1 for r in index if r.get("source") == "raw"),
                      "historical": sum(1 for r in index if r.get("source") == "committed_historical"),
                      "missing": missing}))
    if missing:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
