# Luma source-backed audit handoff

**Implementation commit:** recorded in `manifest.json` after the additive audit/candidate commit. **Base:** `e5608cd053be5376a54a806129a332952dfabcef`. **Verified handoff:** `0aa7bd6ac099fc457179debbf749f0227c714158`. Branch: `arena/0bee657b-lg-luma` only.

## Bottom line

- Native source and protected Home/platform paths are unchanged. No TV was contacted; physical evidence is **NOT_RUN**.
- Luma already owns a coherent Rust/SDL state→scene→renderer architecture, guarded navigation, settings/storage, bounded workers and damage/cache diagnostics. Reuse it; do not import a browser runtime or reference recovery scripts.
- Real video is **not implemented**. Separate supported-player handoff exists; inline video/media-plane feasibility is BLOCKED pending authorized API/copy/lifecycle evidence.
- One bounded default-OFF focus-depth candidate is supplied **unapplied**. It is not a compiled or device-validated implementation.

## Read first

1. `manifest.json` — hashes, provenance, actual exits, blocker IDs and evidence classes.
2. `BLOCKERS.json` — open gates and next actions.
3. `../research/luma-audit/architecture.md` — ownership map and source anchors.
4. `../research/luma-audit/capability-ledger.json` — OBSERVED / UNKNOWN / PROPOSED / BLOCKED inventory.
5. `../research/luma-audit/ux-settings.md`, `rendering-performance.md`, `video-feasibility.md`.
6. `../research/luma-audit/focus-experiment.md`, `patches/focus-depth.patch`, `rollback.md`.
7. `../research/luma-audit/device-validation-plan.md` — separate approval gate; currently NOT-READY.
8. `../research/luma-audit/references.md`, `receipts/index.json` — access/provenance and sanitized raw-receipt hashes.

## Actual execution summary

| Gate | Result | Meaning |
|---|---:|---|
| Handoff blob integrity | 17/17 match | Content matches pinned handoff tree |
| Offline verifier | exit 1 | Python/JSON parse passed; Node stats import missing `streamMetrics.mjs`; assertions did not run |
| Original named Node baseline | exit 1, 36/37 | Release case could not spawn absent pnpm; not repaired |
| Supported Node suites | exit 0, 19/19 | Companion pages only |
| Supported release subset | exit 0, 17/17 | Not the full baseline |
| Independent synthetic evidence/arithmetic tests | exit 0, 16/16 | Unchanged bundled processor + independent helpers; no device measurement |
| Candidate static scope/default-off contract | exit 0 | Text contract only |
| Candidate apply check | exit 1, stopped after two failures | Missing new-file mode header; generator corrected, corrected apply NOT_RUN |
| Native build/tests | BLOCKED / exit 127 availability | 334 static Rust test attributes indexed, none claimed to pass |
| Physical TV | NOT_RUN | No deployment, measurement or mutation |

## Next gate

Restore the documented Rust/SDL/pnpm environment; rerun original baselines without rewriting known failures; obtain the missing authorized statistics module; explicitly resume corrected-patch apply/reverse validation; then compile and run native candidate/regression tests. Only after those gates and separate owner approval should any device preflight/canary occur. Video requires its own approval and evidence.

All calculations/diffs/hashes/receipts are script-generated. Raw outputs remain outside the checkout under `/home/user/luma-research-evidence`; sanitized hash-linked receipts are here. No credentials, firmware archives, HARs, protected media or proprietary Apple code/assets were collected.
