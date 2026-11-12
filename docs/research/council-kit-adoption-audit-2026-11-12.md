# Council kit adoption audit for lg-luma (2026-11-12)

## Status and scope

**REVIEW ONLY / NO DEVICE EXECUTION / NO RUNTIME CHANGES.** This document evaluates a candidate tool bundle in `SteveSpivak/luma-webos-launcher` for selective adoption into this repository. Its presence is not a sign-off for the Nuvio integration or a TV installation.

Source: `SteveSpivak/luma-webos-launcher`, branch `arena/5fe14abb-luma-webos-launcher`, commit `4e6029b654ee2b035052721b9d095a7db1e8d65f`. Source files are under `COUNCIL_STARTER_KIT/`. This target is `SteveSpivak/lg-luma` at `e5608cd053be5376a54a806129a332952dfabcef` when audited. These are **not** interchangeable source trees.

Evidence classes: SOURCE_INSPECTED for the findings below; NOT_RUN for actual target toolkit execution, native build, TV deployment, and installed-host tests. Arena's reported successes are external agent claims, not independent reproduction here.

## Key review findings

1. **CRITICAL: Lab request can resolve to production Nuvio app ID.** In `COUNCIL_STARTER_KIT/nuvio_constraint_validator.py`, the modeled `nuvio_app_id(True, False)` explicitly returns `space.nuvio.webos` and its test **expects** that value. This is incompatible with a strict invariant that explicit lab intent must never launch the production app. Target design: reject unavailable lab feature, do not fall back to production. A default production request is a separate case.
2. **HIGH: Mirror test is not implementation proof.** The 23 Python assertions test copied constants and logic rather than importing/executing the Rust `src/platform.rs` functions. Stage 0 in `council_pipeline.py` calls the mirrored file only. Add Rust negative cases and verify the exact compiled feature combination.
3. **HIGH: Rust scanning absent from bug hunter.** `aegis_bug_hunter.py` defines its source extensions as `.py/.ts/.tsx/.js/.jsx`, omitting `.rs`. Reported anomaly counts and `SAFE_TO_SHIP` cannot establish correctness of the native Rust application.
4. **HIGH: Drift scans the wrong language.** `repo_sync.py:detect_drift_locally` enumerates only the first 50 Python files. A zero-exit drift report means the script ran, not that Rust source drift was excluded. `cmd_drift` always returns zero.
5. **HIGH: Pipeline does not fail fast.** `run_full_pipeline` records failed stages then continues. External scripts may still run after Stage 0 fails. For an enforceable safety gate, return immediately, prevent deployment/ship, and ensure the gate reads current source/build metadata.
6. **MEDIUM: Entrypoint contract needs a direct test.** `council_entry.py` dispatches `validate-constraints` as the first positional argument to `nuvio_constraint_validator.py`, whose top-level module instead runs its assertions immediately. This may exit successfully but does not provide a real command parser/contract.
7. **MEDIUM: Documentation overclaims.** Kit README says 'production-ready' while macOS, Rust compilation, and webOS IPK remain unverified. Compression ratios, performance estimates, AST/CFG and 'zero regression' claims require artifact identity, comparison baselines, reproducible raw measurements and known-bad mutations.
8. **HIGH: Copy instructions are structurally inconsistent.** README says to copy kit files to repository root but examples run `scripts/council_entry.py`. In the source tree they live under `COUNCIL_STARTER_KIT/`, while `repo_sync.py` assumes a `scripts/repo_manifest.json` with source-specific repository aliases. No blind copy.

## Canonical target ownership and constraints

- The target repository's existing `agents.md`, `development.md`, `Cargo.toml`, `src/`, `tv-helper/`, `tests/` and `.github/workflows/ci.yml` are authoritative.
- Current target has `webos` feature, no default Nuvio feature in its audited Cargo.toml. Nuvio source from the research repo must not be silently installed.
- Preserve `com.ecklf.luma` package identity; do not replace stock Home or Nuvio IDs.
- Keep display/input work on SDL thread and TV/HTTP work off-thread. Do not contact a real TV or live APIs in automated tests.
- Existing checks: `pnpm format:check`, `pnpm check`, `pnpm test`, `pnpm assets`, `pnpm test:smoke`, `pnpm run package` according to `agents.md`. Actual native builds and TV tests remain NOT_RUN for this audit.
- All on-TV tests require explicit separate authorization, backup/current-state capture, a known-restorable IPK, and independently rehearsed rollback.

## Reuse / adapt / reject

| Candidate | Decision | Conditions |
| --- | --- | --- |
| SHA-pinned source identity, parent receipts, status taxonomy | ADAPT | Receipt records exact input tree SHA, dirty state, command, exit, output hash and environment; mutable records not called tamper-proof |
| Symbol indexing and localized retrieval | EVALUATE | Compare with `rg`, rust-analyzer, cargo metadata and existing tooling on identical Rust tasks and worktrees |
| Lossless tool-result handles | EVALUATE | Prove retrieval, token counting, privacy boundary, and quality preservation with canaries |
| `aegis` regex bug hunt as Rust verifier | REJECT | No Rust support; use rustc, Clippy, tests, rust-analyzer, targeted semantic checks and mutation fixtures |
| `SAFE_TO_SHIP` from static call-site heuristics | REJECT | Not proof of regression freedom; require tests, artifact provenance and native gates |
| Python mirrored Nuvio constraint test as primary protection | REJECT | Convert assumptions into Rust acceptance tests; explicit lab request must fail closed |
| Cross-repo drift report | REWRITE | Compare pinned actual source trees, parse manifest/features, exact changed symbols and compile/test receipts |
| Automatic ship/deploy as a general pipeline stage | DO NOT ADOPT | Separate review, merge, build and explicitly authorized device deployment |

## Bounded implementation sequence

1. **T0 identity:** Capture the two immutable SHAs, list changed files against target, canonical app IDs, feature definitions and installed-tool versions. Do not update `main` by assumption.
2. **T1 offline evaluation:** In a disposable worktree, execute a *copy* of selected Python tools with scratch `REPO_ROOT`; use a clean fixture root and assert no tracked or target runtime path changes. Record stdout/stderr, exit codes and exact script hashes.
3. **T2 mutation:** Introduce deliberate invalid lab app IDs, disabled feature + lab request, Rust-only drift, broken Rust call sites, and missing manifests. A verifier that returns green on a deliberately bad case is rejected.
4. **T3 native checks:** `cargo test --locked --all-features`, `cargo clippy --locked --all-targets --all-features -- -D warnings`, `cargo fmt --all -- --check`, plus existing pnpm commands in the established target CI. Align flags to supported target combinations rather than assuming feature parity.
5. **T4 integration:** Only after passing mutation tests, propose a separate implementation PR against a current target baseline. Do not merge experimental Rust from source wholesale.
6. **T5 canary:** Manual authorized TV test with backup, unique device/package identity, restore IPK, rollback receipt, and explicit prohibition on playback/autoplay and production Nuvio mutation.

## Acceptance criteria

- The target release/CI ownership stays unchanged; documentation is the only modification in this PR.
- Explicit `lab=true` with a disabled feature produces a **hard error**, not a production launch.
- Rust-only mutations turn the relevant verifier RED.
- Every PASS is tied to exact source SHA and a command exit; BLOCKED, NOT_RUN and UNKNOWN are preserved.
- Pipeline stops before any source mutation, ship or device contact on a failed precondition.
- A later implementation PR must include focused failing-before/passing-after tests, unchanged unrelated source hashes, and a separately approved TV test.

## Commands for the local agent (NOT_RUN here)

```sh
git status --porcelain=v1
git rev-parse HEAD
python3 --version
cargo --version
pnpm --version
# Evaluate selected kit tools only in a scratch copy, not the target root.
# Then run existing lg-luma CI commands exactly as documented in agents.md.
```

Do not mark this integration complete until independently generated local and CI receipts exist.
