# Pinned Council kit snapshot (isolated evaluation)

This folder contains source files copied unchanged from `SteveSpivak/luma-webos-launcher@ff9a6b8a6d793938e6aeef41f1ed1053bbe404df` under `COUNCIL_STARTER_KIT/`. The 18 copied files have Git blob hashes matching the source. The transfer itself does not validate any code correctness.

**Quarantined / NOT INTEGRATED / NOT EXECUTED.** This is not an installed production toolchain. Do not run the full council pipeline against this repository without first adapting paths and writing to an isolated scratch worktree.

Omitted intentionally: source kit nested `.github/workflows/council.yml`, `.pre-commit-config.yaml`, and historical generated `docs/xray/_data/execution_receipts.json`. No source Rust, application ID, manifest, target agent instructions, target CI workflows or release behavior was modified.

Current limitations:
- `aegis_bug_hunter.py` excludes Rust from static source scanning.
- `repo_sync.py` emits a 0 exit status regardless of whether drift is resolved.
- Python Nuvio validator mirrors Rust rather than executing Rust functions.
- Arena `src/tests.rs` at the source ref includes a moved-value assertion using `result.unwrap_err()` twice; compile/run actual Rust tests before transferring any Nuvio implementation.
- Source tools assume a source-repo `scripts/repo_manifest.json` and other paths not present in this isolated folder. No autodeploy/auto-ship permission is given.

Existing `lg-luma` Cargo, pnpm, Ubuntu CI/Xvfb, ARM/webOS package jobs are the canonical verification path. TV testing requires explicit approval, a backup and a reversible IPK.

Evidence: `SOURCE_COPIED_HASH_MATCH`; actual unit, Rust, packaging, Linux runtime and TV verification `NOT_RUN`.
