#!/usr/bin/env python3
"""Forward/reverse patch gate on an isolated, source-pinned copy of src/.

No checkout, branch creation, dependency installation, native build or device
access. Expected negative controls are not retries. Unexpected failures stop.
The application working tree must remain byte-identical throughout.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import re
import subprocess
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "e5608cd053be5376a54a806129a332952dfabcef"
ALLOWED = {"src/main.rs", "src/view.rs", "src/focus_experiment.rs"}
REPORT = ROOT / "research/audit/patch-integrity.json"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def tree_hashes(directory: Path) -> dict[str, str]:
    return {str(p.relative_to(directory)): sha(p.read_bytes())
            for p in sorted((directory / "src").rglob("*")) if p.is_file()}


def validate_scope(data: bytes) -> list[str]:
    text = data.decode("utf-8")
    pairs = re.findall(r"^diff --git a/(\S+) b/(\S+)$", text, re.MULTILINE)
    if not pairs or any(a != b for a, b in pairs) or {a for a, _ in pairs} != ALLOWED:
        raise ValueError("Patch must modify exactly the three allowed source paths")
    if re.search(r"^(rename |copy |deleted file |GIT binary patch|old mode |new mode 120000|new file mode 120000)", text, re.MULTILINE):
        raise ValueError("Renames, deletions, binary patches and symlinks are forbidden")
    section = text.split("diff --git a/src/focus_experiment.rs b/src/focus_experiment.rs\n", 1)[1]
    if not section.startswith("new file mode 100644\n--- /dev/null\n+++ b/src/focus_experiment.rs\n"):
        raise ValueError("New source file requires Git creation metadata (the historical failure)")
    return sorted(ALLOWED)


def extract_base(destination: Path) -> None:
    archive = git("archive", BASE, "src")
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as tar:
        for member in tar.getmembers():
            path = Path(member.name)
            if path.is_absolute() or ".." in path.parts or not path.parts or path.parts[0] != "src":
                raise ValueError(f"Unexpected source archive member: {member.name}")
            if member.isdir():
                continue
            if not member.isfile():
                raise ValueError(f"Non-regular source archive member: {member.name}")
            target = destination / path
            target.parent.mkdir(parents=True, exist_ok=True)
            stream = tar.extractfile(member)
            if stream is None:
                raise ValueError(f"Unreadable archive member: {member.name}")
            target.write_bytes(stream.read())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--patch", type=Path, default=ROOT / "delivery/patches/focus-depth.patch")
    parser.add_argument("--expected-sha256", help="Default: candidate hash in delivery/manifest.json")
    args = parser.parse_args()
    patch = args.patch.resolve()
    data = patch.read_bytes()
    expected = args.expected_sha256 or json.loads((ROOT / "delivery/manifest.json").read_text())["candidate_patch"]["sha256"]
    if sha(data) != expected:
        raise SystemExit("Patch hash differs from the manifest; refusing integrity gate")
    paths = validate_scope(data)
    before = tree_hashes(ROOT)
    steps = []

    def run(name: str, argv: list[str], cwd: Path, expect_zero: bool) -> None:
        result = subprocess.run(argv, cwd=cwd, capture_output=True, timeout=30, check=False)
        passed = (result.returncode == 0) if expect_zero else (result.returncode == 1 and b"patch does not apply" in result.stderr)
        def clean(value: bytes) -> str:
            return value.decode("utf-8", "replace").replace(str(ROOT), "<CHECKOUT>").replace(str(cwd), "<SCRATCH>")
        steps.append({"name": name, "argv": [v.replace(str(ROOT), "<CHECKOUT>").replace(str(cwd), "<SCRATCH>") for v in argv],
                      "expected": "exit 0" if expect_zero else "nonzero exit; no application",
                      "exit_code": result.returncode, "status": "PASS" if passed else "FAIL",
                      "stdout_sha256": sha(result.stdout), "stderr_sha256": sha(result.stderr),
                      "stdout": clean(result.stdout), "stderr": clean(result.stderr)})
        if not passed:
            raise RuntimeError(f"{name}: exit {result.returncode}; {clean(result.stderr)}")

    # Must be outside every Git worktree: git apply can skip ignored .build paths.
    build = ROOT.parent / "luma-patch-integrity"
    build.mkdir(parents=True, exist_ok=True)
    succeeded = False
    outside_git = False
    failure = None
    candidate_hashes = {}
    try:
        with tempfile.TemporaryDirectory(prefix="focus-", dir=build) as temporary:
            scratch = Path(temporary)
            probe = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=scratch, capture_output=True, check=False)
            outside_git = probe.returncode != 0
            if not outside_git:
                raise RuntimeError("Scratch directory is inside a Git worktree; refusing a potentially ignored no-op")
            extract_base(scratch)
            baseline = tree_hashes(scratch)
            if baseline != before or "src/focus_experiment.rs" in baseline:
                raise RuntimeError("Application src/ differs from the pinned base before the gate")
            run("reverse_on_baseline_rejected", ["git", "apply", "--reverse", "--check", str(patch)], scratch, False)
            run("forward_check", ["git", "apply", "--check", str(patch)], scratch, True)
            run("forward_apply", ["git", "apply", str(patch)], scratch, True)
            applied = tree_hashes(scratch)
            changed = {p for p in set(baseline) | set(applied) if baseline.get(p) != applied.get(p)}
            if changed != ALLOWED:
                raise RuntimeError(f"Unexpected applied paths: {sorted(changed)}")
            candidate_hashes = {p: applied[p] for p in paths}
            run("double_apply_rejected", ["git", "apply", "--check", str(patch)], scratch, False)
            run("reverse_check", ["git", "apply", "--reverse", "--check", str(patch)], scratch, True)
            run("reverse_apply", ["git", "apply", "--reverse", str(patch)], scratch, True)
            if tree_hashes(scratch) != baseline:
                raise RuntimeError("Reverse application did not restore every source byte")
            view = scratch / "src/view.rs"
            original = view.read_bytes()
            context = b"if focused { 34. } else { 22. },"
            if original.count(context) != 1:
                raise RuntimeError("Stale-source control lost its unique patch context")
            view.write_bytes(original.replace(context, b"if focused { 35. } else { 22. },", 1))
            run("stale_source_rejected", ["git", "apply", "--check", str(patch)], scratch, False)
            succeeded = tree_hashes(ROOT) == before and sha(patch.read_bytes()) == expected
            if not succeeded:
                raise RuntimeError("Application source or patch changed during the gate")
    except Exception as error:
        failure = str(error).replace(str(ROOT), "<CHECKOUT>")
    result = {"schema": "luma-patch-integrity/1", "base_sha": BASE,
              "checkout_head_sha": git("rev-parse", "HEAD").decode().strip(),
              "patch_sha256": sha(data), "patch_bytes": len(data), "paths": paths,
              "base_tree_sha": git("rev-parse", f"{BASE}^{{tree}}").decode().strip(),
              "src_tree_sha": git("rev-parse", f"{BASE}:src").decode().strip(),
              "candidate_file_sha256": candidate_hashes,
              "forward_apply": any(s["name"] == "forward_apply" and s["status"] == "PASS" for s in steps),
              "reverse_apply": any(s["name"] == "reverse_apply" and s["status"] == "PASS" for s in steps),
              "application_source_unchanged": tree_hashes(ROOT) == before,
              "scratch_outside_git_repository": outside_git,
              "all_passed": succeeded, "failure": failure, "steps": steps,
              "scope": "Git patch integrity only; Rust compilation, native behavior and TV tests NOT_RUN."}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"all_passed": succeeded, "patch_sha256": sha(data),
                      "steps": {s["name"]: s["exit_code"] for s in steps}, "failure": failure}))
    return 0 if succeeded else 1


if __name__ == "__main__":
    raise SystemExit(main())
