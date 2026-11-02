# Luma audit follow-up handoff

**Base:** `e5608cd053be5376a54a806129a332952dfabcef`. **Updated handoff:** `2a40c7bb3af080981653f975b5c1e983e4f78ef5`. **Audit start HEAD:** `b94cea3b43560e4bda595bc13d88d658a532331f`. Branch: `arena/0bee657b-lg-luma` only. Implementation commit: `47c166c70a6acae9f4ee3fd92cec5fc2098bdde1`. The dedicated branch was pushed and remote-verified at `921d92fb26e4defe0f5e5c3a1b114f2151822908`; no merge was performed. Native validation prep commit: `bb0c2e4bacc232cde50c9c6e88dbc09abe56ddcf`. Native desktop validation is prepared in `NATIVE-VALIDATION.md` and currently BLOCKED by missing tools.

## Current verdict

- Updated handoff verified: **18/18 blobs**, no extras. Offline verifier rerun once: **exit 0**, **11/11 Node assertions**, two Python parses and four JSON parses.
- Focus-depth patch integrity gate: **PASS**. Forward/reverse check+apply exited 0; reverse-on-baseline, double-apply and stale-context controls exited 1 as expected. Application source stayed byte-identical. Patch remains **unapplied**; native behavior is still BLOCKED.
- Final Python research/tooling suite: **31/31**, exit 0. This is not native Rust/SDL validation.
- Manual build-environment specification prepared from Cargo/pnpm/Nix/CI pins. **Nothing installed, downloaded, built or deployed.**
- Native source/protected paths unchanged. No TV contacted; physical evidence **NOT_RUN**.

## Read first

1. `SCORECARD.md` — short evidence-backed status and next smallest experiment.
2. `manifest.json` — exact SHAs, hashes, exits, evidence classes and blocker IDs.
3. `PATCH-INTEGRITY.md` — historical failure diagnosis and final isolated gate.
4. `BUILD-ENVIRONMENT.md` / `build-environment.json` — manual reference environment and reproducibility gaps.
5. `PERFORMANCE-PROPOSALS.md` — wallpaper spikes, vector cache, input/p99 diagnostics, focus candidate, video ordering.
6. `BLOCKERS.json` — B03/B05 resolved; B01/B02/B04/B06/B07/B08 remain open.
7. Existing audit: `../research/luma-audit/` (architecture, capability ledger, rendering, UX/settings, video, device plan, references).

## Tooling accuracy fixes

- Receipt collector now reads the actual runner schema (`argv`, `head`, `outputs`) and backfills historical sanitized receipts from raw files; earlier null provenance fields are corrected without rerunning old tests.
- Handoff verifier is reusable and checks exact commit/ref, every pinned blob and extra files.
- Patch gate uses an external non-Git scratch directory, post-apply hash assertions and expected negative controls; ignored `.build` no-op behavior is explicitly rejected.
- Offline diagnostics analyzer derives nearest-rank p99 from existing timelines and keeps missing native/GPU/focus data UNKNOWN.

## Next gates

Restore the manual reference environment; rerun original baselines unchanged; run supplied Rust focus/damage tests and the bounded desktop focus A/B. Then add instrumentation-only cold-wallpaper/vector active-set and input-to-visible-call/p99 measurements before worker decode, eviction or video work. Device and video require separate approval.

Raw outputs remain outside the checkout under `/home/user/luma-research-evidence`; sanitized hash-linked receipts are in `receipts/`. No credentials, firmware archives, HARs, protected media or proprietary Apple code/assets were collected.
