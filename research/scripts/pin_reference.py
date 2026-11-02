#!/usr/bin/env python3
"""Read small GitHub reference files at an immutable SHA; no clones or execution.

Raw metadata/files and receipts stay outside the checkout. With no --path, list
candidate instruction/research paths. Each downloaded blob is checked against
its pinned Git tree SHA. A request is attempted once; no automatic retry.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://api.github.com/repos/"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def request(url: str, raw: bool = False) -> bytes:
    headers = {"User-Agent": "Luma-pinned-reference-audit", "Accept": "application/vnd.github+json"}
    if raw:
        headers["Accept"] = "application/vnd.github.raw+json"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        data = response.read(2 * 1024 * 1024 + 1)
    if len(data) > 2 * 1024 * 1024:
        raise ValueError("Reference exceeds the 2 MiB per-file collection limit")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--path", action="append", default=[])
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repo) or not re.fullmatch(r"[0-9a-f]{40}", args.sha):
        parser.error("Use owner/repo and a full lowercase commit SHA")
    root = Path.cwd().resolve()
    out = args.out.resolve()
    if out == root or root in out.parents:
        parser.error("Raw reference output must be outside the checkout")
    out = out / args.repo.replace("/", "__") / args.sha
    out.mkdir(parents=True, exist_ok=True)
    receipt = {"schema": "luma-reference-receipt/1", "repo": args.repo, "requested_sha": args.sha, "collected_utc": datetime.now(timezone.utc).isoformat(), "files": [], "label": "UNKNOWN"}
    try:
        commit_path, tree_path = out / "commit.json", out / "tree.json"
        if not commit_path.exists():
            commit_path.write_bytes(request(API + f"{args.repo}/commits/{args.sha}"))
        commit = json.loads(commit_path.read_bytes())
        if commit.get("sha") != args.sha or "commit" not in commit:
            raise ValueError("GitHub did not resolve the exact requested commit")
        receipt["verified_commit"] = commit["sha"]
        receipt["tree_sha"] = commit["commit"]["tree"]["sha"]
        if not tree_path.exists():
            tree_path.write_bytes(request(API + f"{args.repo}/git/trees/{receipt['tree_sha']}?recursive=1"))
        tree = json.loads(tree_path.read_bytes())
        if tree.get("truncated"):
            raise ValueError("GitHub tree is truncated; file coverage is incomplete")
        entries = {entry["path"]: entry for entry in tree["tree"] if entry["type"] == "blob"}
        receipt["tree_entries"] = len(entries)
        receipt["label"] = "PROVEN"
        if not args.path:
            pattern = re.compile(r"(^|/)(AGENTS\.md|agents\.md|CLAUDE\.md|HANDOFF\.md|manifest\.json|.*\.schema\.json|stats\.mjs|EXPERIMENT-CLI\.md|known-fail-signatures\.json|ARCHITECTURE\.md|correlate\.py)$|SharedHero|HeroCard|Focus|focus|Trailer|trailer|Ambient|ambient|Settings|settings|BackHandler|backHandler", re.IGNORECASE)
            receipt["candidate_paths"] = [path for path in sorted(entries) if pattern.search(path)]
        for relative in args.path:
            if relative not in entries or relative.startswith("/") or ".." in Path(relative).parts:
                raise ValueError(f"Path not present in pinned tree: {relative}")
            data = request(API + f"{args.repo}/contents/{relative}?ref={args.sha}", raw=True)
            blob_sha = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
            if blob_sha != entries[relative]["sha"]:
                raise ValueError(f"Pinned blob mismatch for {relative}")
            destination = out / "files" / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            receipt["files"].append({"path": relative, "git_blob_sha1": blob_sha, "sha256": digest(data), "bytes": len(data), "local_path": str(destination)})
    except (urllib.error.URLError, ValueError, KeyError, TimeoutError) as error:
        receipt["label"] = "BLOCKED"
        receipt["error"] = str(error)
    receipt["metadata_sha256"] = {p.name: digest(p.read_bytes()) for p in (out / "commit.json", out / "tree.json") if p.exists()}
    receipt_path = out / ("receipt-" + digest((":".join(args.path)).encode())[:12] + ".json")
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({**receipt, "receipt": str(receipt_path)}, indent=2))
    return 0 if receipt["label"] == "PROVEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
