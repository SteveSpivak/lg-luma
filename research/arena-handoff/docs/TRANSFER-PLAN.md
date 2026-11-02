# Reuse plan: source-pinned references, no bulk imports

This handoff is original documentation and an offline reference-index script. It does NOT contain or authorize uploads of proprietary firmware, binaries, credentials, HARs, protected media or full external source trees.

## Transfer/adapt after commit verification
- **nuvio-perf-lab**: `lab/perf/EXPERIMENT-CLI.md`, `lab/perf/stats.mjs`, hand-computed statistics tests and `lab/checks/known-fail-signatures.json` for methodological reference. Implement metrics in native Rust or standalone offline Python, not CDP against Luma.
- **Nuvio V5 and upstream**: approved design references for Shared Hero/cards/focus/Back/trailer behavior. Adapt geometry and behavioral contracts to Rust scene/state; don't copy DOM/CSS as implementation.
- **webos-lens**: `contracts/lens-evidence.schema.json`, `cli/correlate.py`, sanitized fixtures, delivery HANDOFF; extend independent evidence contracts, not a second device collector.
- **LG-TV**: `contracts/feature-dependencies.json`, `contracts/device-preflight.schema.json`, delivery HANDOFF. Read-only recovery rules only; do not import rooting, DNS, install or Home-hook scripts.
- **Firmware lab**: `docs/ARCHITECTURE.md` and sanitized dependency metadata only. Its specimen is not proof of running-device dependencies.
- **lg-luma**: authoritative target source; existing renderer/input/settings/tests take priority.

## Exclude
Entire external repository histories, unreviewed images/assets, logs with full IDs/URLs/secrets, firmware archives, IPKs, DRM components, copied Apple artwork, credential and account dumps, and all persistent device mutation.

## Proposed output
Use existing Luma conventions first. If absent: `research/` for ledgers, ADRs, geometry and media-plane analysis; `tests/` for deterministic regressions; `delivery/` for manifest, HANDOFF, blockers and rollback. Raw receipts in a separate ignored/private output directory.

A0 integrity/baseline → A1 ownership map → A2 cards/settings pattern research → A3 media-plane feasibility → A4 one default-OFF prototype → A5 offline regression → A6 optional owner-approved device canary.
