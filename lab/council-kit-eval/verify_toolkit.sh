#!/usr/bin/env bash
# Reproducible verification of the Council toolkit at its actual location.
#
# Every check prints PASS/FAIL/BLOCKED with the command that produced it. Nothing
# here mutates the toolkit: the Stage 0 mutation test runs in a throwaway git
# worktree that this script creates and removes.
#
# Usage:
#   lab/council-kit-eval/verify_toolkit.sh
#   COUNCIL_KIT=/path/to/lab/council-kit lab/council-kit-eval/verify_toolkit.sh
#
# Exit code: 0 only if every check that could run did pass. Checks that cannot
# run are reported BLOCKED and do not fail the script; a FAIL does.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${REPO_ROOT:-$(cd "$HERE/../.." && pwd)}"
KIT="${COUNCIL_KIT:-$REPO_ROOT/lab/council-kit}"
EVAL_KIT="$REPO_ROOT/lab/council-kit"   # the branch under evaluation, if present
WORKTREE=""

fails=0; blocks=0
say()  { printf '%s\n' "$*"; }
ok()   { say "PASS    $*"; }
bad()  { say "FAIL    $*"; fails=$((fails+1)); }
skip() { say "BLOCKED $*"; blocks=$((blocks+1)); }

cleanup() {
  if [ -n "$WORKTREE" ] && [ -d "$WORKTREE" ]; then
    git -C "$REPO_ROOT" worktree remove --force "$WORKTREE" >/dev/null 2>&1
  fi
}
trap cleanup EXIT

say "=============================================================="
say " Council toolkit verification"
say "=============================================================="
say "repo root : $REPO_ROOT"
say "toolkit   : $KIT"
say ""

# ---------------------------------------------------------------- 1. presence
say "--- 1. toolkit location ---"
if [ -f "$KIT/aegis_bug_hunter.py" ]; then
  ok "toolkit found at $KIT"
else
  skip "toolkit not present at $KIT"
  say "        It lives on branch lab/council-kit-snapshot-ff9a6b8-20261113 (PR #2)."
  say "        Set COUNCIL_KIT to a checkout of that branch to run the rest."
  # Fall back to the eval directory if this script is run on that branch.
  if [ -f "$EVAL_KIT/aegis_bug_hunter.py" ]; then KIT="$EVAL_KIT"; ok "using $KIT"; else exit 2; fi
fi

# ------------------------------------------------------- 2. shipped self-test
say ""
say "--- 2. shipped self-test (expected to fail at step 8) ---"
out="$(cd "$REPO_ROOT" && timeout 600 python3 "$KIT/tests/test_starter_kit.py" 2>&1)"
rc=$?
if [ $rc -eq 0 ]; then
  ok "test_starter_kit.py: 9/9 (manifest dependency now satisfied)"
else
  nfail="$(printf '%s' "$out" | grep -c '^   - ')"
  if printf '%s' "$out" | grep -q "repo_manifest.json"; then
    bad "test_starter_kit.py: ${nfail} failure(s) — missing scripts/repo_manifest.json"
  else
    # The self-test only prints "rc=1, err=" because the pipeline captures the
    # subprocess traceback. Reproduce the underlying command to get the real cause.
    bad "test_starter_kit.py: ${nfail} failure(s) at step 8 (exit $rc)"
    cause="$(cd "$KIT" && REPO_ROOT="$REPO_ROOT" timeout 120 python3 repo_sync.py drift 2>&1 | tail -3)"
    say "        underlying cause of step 8 (repo_sync.py drift):"
    printf '%s\n' "$cause" | sed 's/^/        /'
  fi
  printf '%s\n' "$out" | grep -E "^(SELF-TEST|[0-9]+\. )" | sed 's/^/        /'
fi

# ------------------------------------------------------- 3. Stage 0 fail-fast
say ""
say "--- 3. Stage 0 fail-fast under a negative mutation ---"
# Base the worktree on the commit that actually contains the toolkit, and use the
# toolkit's path inside its own repository (not a path relative to $REPO_ROOT,
# which may be a different checkout).
KIT_REPO="$(git -C "$KIT" rev-parse --show-toplevel 2>/dev/null)"
KIT_SUB="$(git -C "$KIT" rev-parse --show-prefix 2>/dev/null)"
BASE_REF="$(git -C "$REPO_ROOT" rev-parse --verify --quiet \
              origin/lab/council-kit-snapshot-ff9a6b8-20261113 2>/dev/null)"
[ -n "$BASE_REF" ] || BASE_REF="${KIT_REPO:+$(git -C "$KIT_REPO" rev-parse HEAD)}"
[ -n "$BASE_REF" ] || BASE_REF="$(git -C "$REPO_ROOT" rev-parse HEAD)"
KIT_SUB="${KIT_SUB%/}"
[ -n "$KIT_SUB" ] || KIT_SUB="lab/council-kit"
WORKTREE="$(mktemp -d /tmp/council-mut-XXXXXX)"
rmdir "$WORKTREE"
say "        worktree base: $(git -C "$REPO_ROOT" rev-parse --short "$BASE_REF" 2>/dev/null || echo "$BASE_REF")  kit subdir: $KIT_SUB"
if git -C "$REPO_ROOT" worktree add --detach "$WORKTREE" "$BASE_REF" >/dev/null 2>&1; then
  MUTDIR="$WORKTREE/$KIT_SUB"
  mut="$MUTDIR/nuvio_constraint_validator.py"
  if [ -f "$mut" ]; then
    if python3 - "$mut" <<'PY'
import sys
p=sys.argv[1]; s=open(p).read()
old="""    if lab:
        if feature_nuvio_lab:
            return NUVIO_LAB_APP_ID"""
new="""    if lab:
        if feature_nuvio_lab:
            return NUVIO_APP_ID  # MUTATION: unsafe fallback to production"""
assert s.count(old)==1, "mutation anchor not unique"
open(p,"w").write(s.replace(old,new))
PY
    then
      before="$(find "$WORKTREE" -path "$WORKTREE/.git" -prune -o -type f -print | sort | xargs sha256sum 2>/dev/null)"
      mout="$(cd "$MUTDIR" && REPO_ROOT="$WORKTREE" timeout 300 python3 council_entry.py full --workers 2 2>&1)"
      mrc=$?
      stages="$(printf '%s' "$mout" | grep -oE "Stages completed: [0-9]+" | grep -oE "[0-9]+")"
      if [ "$mrc" -ne 0 ] && [ "$stages" = "1" ] && printf '%s' "$mout" | grep -q "PIPELINE HALTED"; then
        ok "mutation -> exit $mrc, halted after stage $stages, receipt $(printf '%s' "$mout" | grep -oE 'RCPT-[0-9A-F]+' | head -1)"
      else
        bad "mutation did not halt the pipeline (exit=$mrc stages=$stages)"
      fi
      # restore and re-check
      git -C "$WORKTREE" checkout -- . >/dev/null 2>&1
      rout="$(cd "$MUTDIR" && REPO_ROOT="$WORKTREE" timeout 300 python3 council_entry.py full --workers 2 2>&1)"
      if printf '%s' "$rout" | grep -q "Stage 1 \[PASS\] nuvio_constraint_validate"; then
        ok "restore -> Stage 0 GREEN again"
      else
        bad "restore did not return Stage 0 to GREEN"
      fi
    else
      bad "could not apply the Stage 0 mutation (anchor changed?)"
    fi
  else
    skip "validator not found inside the mutation worktree"
  fi
else
  skip "could not create a git worktree for the mutation test"
fi

# ---------------------------------------------------------- 4. drift exit code
say ""
say "--- 4. drift: reporting vs enforcement ---"
tmpd="$(mktemp -d /tmp/council-drift-XXXXXX)"
python3 - "$KIT/repo_sync.py" "$tmpd" <<'PY'
import json, subprocess, sys, os
from pathlib import Path
kit, root = Path(sys.argv[1]), Path(sys.argv[2])
(root/"scripts").mkdir(parents=True, exist_ok=True)
(root/"scripts"/"repo_manifest.json").write_text(json.dumps(
    {"repos": {"lg-luma": {"last_known_head": "x"}}, "alignment_rules": [], "drift_categories": []}))
d = root/"driftprobe"; d.mkdir(exist_ok=True)
for i in range(210):                       # push the marker past the old 200-file limit
    (d/f"filler_{i:04d}.py").write_text(f"X_{i}=0\n")
(d/"zz_deep_drift.rs").write_text('pub const BAD: &str = "space.nuvio.webos";\n')
env = {**os.environ, "REPO_ROOT": str(root)}
p = subprocess.run([sys.executable, str(kit), "drift"], capture_output=True, text=True, cwd=root, env=env)
found = "zz_deep_drift" in p.stdout
print(f"        marker detected beyond the 200-file boundary : {found}")
print(f"        exit code                                    : {p.returncode}")
sys.exit(0 if not found else (10 if p.returncode == 0 else 11))
PY
case $? in
  10) bad  "drift detected real drift but still exited 0 (reporting only, not a gate)";;
  11) ok   "drift now fails closed on detected drift";;
  *)  bad  "drift did not detect the planted marker";;
esac
rm -rf "$tmpd"

# -------------------------------------------------- 5. Aegis Rust precision/recall
say ""
say "--- 5. Aegis Rust scanner precision / recall ---"
if COUNCIL_KIT="$KIT" python3 "$HERE/aegis_rust_eval.py" 2>&1 | tail -12 | sed 's/^/        /'; then
  ok "Aegis Rust scanner meets the configured thresholds"
else
  bad "Aegis Rust scanner below threshold (see REPORT.md section 7)"
fi

# ----------------------------------------------------------- 6. Rust toolchain
say ""
say "--- 6. Rust / webOS validation ---"
for tool in cargo rustc pkg-config pnpm xvfb-run; do
  if command -v "$tool" >/dev/null 2>&1; then ok "$tool available"; else skip "$tool not installed"; fi
done
if command -v cargo >/dev/null 2>&1; then
  ( cd "$REPO_ROOT" && cargo fmt --all -- --check && ok "cargo fmt" ) || bad "cargo fmt"
else
  skip "cargo fmt/check/test/clippy — no toolchain (see REPORT.md section 8a)"
fi

say ""
say "=============================================================="
say " failures: $fails   blocked: $blocks"
say "=============================================================="
[ "$fails" -eq 0 ]
