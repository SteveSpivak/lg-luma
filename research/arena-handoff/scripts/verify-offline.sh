#!/usr/bin/env bash
# Offline contract verification. No network, TV, installs, or source mutation.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
LAB="$ROOT/offline-lab"
echo 'Source-pinned offline handoff checks'
if command -v python3 >/dev/null 2>&1; then
  python3 - "$ROOT" "$LAB" <<'PY'
import ast,json,pathlib,sys
root=pathlib.Path(sys.argv[1]); lab=pathlib.Path(sys.argv[2])
for f in [lab/"cli/evidence_tools.py",lab/"cli/correlate.py"]:
    ast.parse(f.read_text(encoding="utf8"),filename=str(f))
    print("PARSE PASS",f.name)
for f in [root/"references/lg-feature-dependencies.json",
          root/"references/lg-device-preflight.schema.json",
          root/"references/lens-evidence.schema.json",
          root/"contracts/reference-manifest.json"]:
    json.loads(f.read_text(encoding="utf8"))
    print("JSON PASS",f.name)
PY
else echo 'BLOCKED python3 not found'; fi
if command -v node >/dev/null 2>&1; then
  node --test "$LAB/lab/checks/experiment-stats.test.mjs"
else echo 'BLOCKED node not found (stats tests NOT_RUN)'; fi
echo 'NOTE: Rust/Cargo/SDL/TV tests are NOT_RUN by this script.'
