# Focus-depth patch integrity gate

**Result: PASS for Git patch integrity only.** Native Rust/SDL compilation/behavior and physical-TV tests remain BLOCKED/NOT_RUN.

- Base: `e5608cd053be5376a54a806129a332952dfabcef`
- Patch: `patches/focus-depth.patch`
- SHA-256: `8230cce60f85db4965f0731e702216dbb5fe7442ee0a33ba4768f9dc0b24a257` (3,779 bytes)
- Paths: `src/main.rs`, `src/view.rs`, new `src/focus_experiment.rs`
- Machine report: `../research/audit/patch-integrity.json`

## Historical failure diagnosis

Saved stderr from both original apply attempts is identical: `error: dev/null: No such file or directory` (SHA-256 `8406467937a711cd03503de2296f1d25183cd93c59d55dcb0ec8c0d6aa0b75a0`). The original generated new-file diff lacked `new file mode 100644`; the corrected generator emits it. The exact malformed bytes were not retained before the first commit, so no hash is claimed for them. The committed artifact is the corrected one; its hash did not change during this follow-up.

Two new harness failures were also retained rather than hidden: first, the archive extractor rejected the `src` directory member before any apply command ran; second, a scratch directory under ignored `.build/` made `git apply --reverse --check` a no-op. The final harness uses a temporary directory **outside every Git worktree**, asserts that isolation, and verifies applied/restored file hashes. This prevents a false PASS from ignored paths.

## Final isolated gate

| Control | Exit | Verdict |
|---|---:|---|
| Reverse check on baseline | 1 | Expected rejection |
| Forward check | 0 | PASS |
| Forward apply | 0 | PASS; exactly three allowed paths changed |
| Double-apply check | 1 | Expected rejection |
| Reverse check | 0 | PASS |
| Reverse apply | 0 | PASS; every source byte restored |
| Stale patch-context check | 1 | Expected rejection |

Application `src/` remained byte-identical to the base throughout. The scratch directory was outside Git. The Python research suite also reruns the original static/default-off contract and a normal `git apply --check` against the unchanged checkout.

This closes the **patch applicability/rollback** blocker, not the native build blocker. Do not deploy or claim visual/performance behavior from this gate.
