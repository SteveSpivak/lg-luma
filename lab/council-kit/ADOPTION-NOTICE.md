# Council toolkit: pinned isolated snapshot and delta

Initial transfer: 18 untouched toolkit source/documentation files from `SteveSpivak/luma-webos-launcher@ff9a6b8a6d793938e6aeef41f1ed1053bbe404df` (matching source Git blob hashes). The `aegis_bug_hunter.py` file was updated from newer source commit `4debf5ed9eba06c0b71dca79b0c7f61aeacec112` (matching blob `a79a9310728542a6ad98bcaeb069e2211a39f361`). All other copied toolkit files remain at the initial snapshot revision.

The newer Arena commit also fixes a Rust negative-test assertion in `src/tests.rs`. That source file was **not** copied to lg-luma: application source and test suites in the two repositories have different ownership. Validate Rust changes separately before considering any port.

**ISOLATED / NOT INTEGRATED / NOT EXECUTED.** This is a source-only research copy; do not treat it as an installed or certified toolchain, run its `ship` actions, or execute its full pipeline against the live target checkout without adapting paths/manifest and sandboxing generated output.

Omitted intentionally: source kit nested `.github/workflows/council.yml`, `.pre-commit-config.yaml`, and mutable historical `execution_receipts.json`. No Rust app source, IDs, target CI or build scripts have been changed.

Remaining limits:
- Aegis now scans `.rs` but its Rust analyzer is regex/line based, not AST/CFG proof; in particular same-line unwrap heuristic is insufficient to establish actual panic safety.
- `repo_sync.py` still returns success for drift reporting rather than enforcing cross-repo equivalence.
- Python constraint validator mirrors Rust and does not execute real Rust code.
- Original source tools assume paths/manifests from the source repository and are not immediately runnable in this destination.
- `lg-luma` already has canonical Ubuntu 24.04 Rust tests, SDL/Xvfb smoke testing and webOS ARM/IPK packaging; preserve those.

**Evidence status:** copied source blobs match upstream; local Rust, Linux CI, packaging, and TV verification **NOT_RUN**. No TV contact without explicit approval, backup, restore IPK and rollback verification.
