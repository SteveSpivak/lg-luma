#!/usr/bin/env python3
"""Verify an extracted handoff against an immutable local Git commit; no network.

Usage: python3 -B research/scripts/verify_handoff.py FULL_SHA [--ref REF]
Only research/arena-handoff is inspected. No checkout, installation or execution
of bundled code occurs. Output: research/audit/handoff-integrity.json.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREFIX = "research/arena-handoff"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def digest(data: bytes) -> dict:
    return {"sha256": hashlib.sha256(data).hexdigest(),
            "git_blob_sha1": hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest(),
            "bytes": len(data)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("commit")
    parser.add_argument("--ref", help="Optional already-fetched ref that must match commit")
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.commit):
        parser.error("A full lowercase 40-character commit SHA is required")
    resolved = git("rev-parse", f"{args.commit}^{{commit}}")
    if resolved != args.commit or (args.ref and git("rev-parse", args.ref) != args.commit):
        raise SystemExit("Commit/ref identity mismatch")
    paths = git("ls-tree", "-r", "--name-only", args.commit, "--", PREFIX).splitlines()
    files, errors = [], []
    for path in paths:
        expected = subprocess.check_output(["git", "show", f"{args.commit}:{path}"], cwd=ROOT)
        local = ROOT / path
        row = {"path": path, "expected": digest(expected)}
        if local.is_file():
            actual = local.read_bytes()
            row.update(actual=digest(actual), matches=actual == expected)
        else:
            row.update(actual=None, matches=False)
        if not row["matches"]:
            errors.append(path)
        files.append(row)
    expected_set = set(paths)
    extras = [str(p.relative_to(ROOT)) for p in (ROOT / PREFIX).rglob("*")
              if p.is_file() and str(p.relative_to(ROOT)) not in expected_set]
    result = {"schema": "luma-handoff-integrity/2", "commit_sha": args.commit,
              "tree_sha": git("rev-parse", f"{args.commit}^{{tree}}"),
              "verified_ref": args.ref, "file_count": len(files),
              "all_match": not errors and not extras, "mismatches": errors,
              "untracked_extra_files": extras, "files": files,
              "scope": "Local Git blob identity only; not upstream-origin or execution proof."}
    output = ROOT / "research/audit/handoff-integrity.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"commit_sha": args.commit, "files": len(files),
                      "all_match": result["all_match"], "extras": extras, "errors": errors}))
    return 0 if result["all_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
