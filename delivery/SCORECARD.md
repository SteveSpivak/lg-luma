# Luma follow-up scorecard

| Gate | Result | Evidence |
|---|---|---|
| Updated handoff | `2a40c7bb3af080981653f975b5c1e983e4f78ef5`; 18/18 blobs, no extras | `receipts/handoff-update-integrity.json` |
| Offline verifier | Exit **0**; 11/11 Node assertions; 2 Python + 4 JSON parses | `receipts/verify-offline-updated.json` |
| Focus patch integrity | Exit **0**; forward/reverse 0; three expected negatives 1; source unchanged | `receipts/patch-integrity-isolated.json`, `PATCH-INTEGRITY.md` |
| Research/tooling tests | Exit **0**; 31/31 Python contracts | `receipts/research-tests-final-corrected.json` |
| Build environment spec | Exit **0**; manual only, no installs/downloads/builds | `build-environment.json`, `BUILD-ENVIRONMENT.md` |
| Native Rust/Cargo/SDL | **BLOCKED**; toolchain absent | `BLOCKERS.json:B01` |
| Full original Node baseline | Historical exit **1**, 36/37; pnpm absent; not rewritten | `BLOCKERS.json:B02` |
| Physical TV / video | **NOT_RUN**; no device contact | `BLOCKERS.json:B07` |

**Exact artifacts:** base `e5608cd053be5376a54a806129a332952dfabcef`; patch SHA-256 `8230cce60f85db4965f0731e702216dbb5fe7442ee0a33ba4768f9dc0b24a257`; previous delivery HEAD `b94cea3b43560e4bda595bc13d88d658a532331f`. Current implementation commit: `47c166c70a6acae9f4ee3fd92cec5fc2098bdde1`.

**Resolved:** missing offline dependency (B03); patch apply/reverse integrity (B05). **Open:** native toolchain (B01), full pnpm baseline (B02), blocked remote reference origins (B04), full JSON-Schema validator (B06), TV/media approval/evidence (B07), native latency/idle/memory instrumentation (B08).

**Priority proposals:** (1) measure cold wallpaper decode/upload and protect visible cache generation during prepare; (2) incremental vector GPU-buffer accounting then measured default-OFF eviction; (3) nearest-rank p99 plus input-dequeue-to-first-swap-call traces; (4) run the integrity-verified default-OFF focus candidate; (5) video only after instrumentation and separate approval.

**Next smallest experiment:** once the manual desktop environment is available, run the already-integrity-verified focus candidate as a bounded unset-vs-`LUMA_FOCUS_DEPTH=1` A/B with isolated preferences, identical assets/scripts, supplied Rust tests and existing damage/focus/Back regressions. No TV, no persistent setting, no new library. Wallpaper worker/eviction changes wait for instrumentation-only baseline measurements.
