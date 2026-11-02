# Offline tools status

Bundled source-pinned offline scripts:
- `offline-lab/lab/perf/stats.mjs` and `offline-lab/lab/checks/experiment-stats.test.mjs` from Nuvio performance lab `fe27abf4`.
- `offline-lab/cli/evidence_tools.py` and `offline-lab/cli/correlate.py` from webos-lens `e5811544`.
- Static reference contracts under `references/`.

Run `bash research/arena-handoff/scripts/verify-offline.sh` in the checked-out handoff branch. This has not yet been executed in Arena, so no PASS is claimed. Node and Python standard library are required for the checks. Missing runtimes are BLOCKED.

Not bundled: privileged device actions, firmware analysis binaries, full browser experiment controller, full device fixtures or native Rust/Cargo/SDL toolchain. Keep TV mutations approval-gated and native tests NOT_RUN until a toolchain is actually present.
