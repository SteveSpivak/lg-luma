# Council Toolkit — Independent Evaluation of `lab/council-kit/` in `lg-luma`

Branch: `arena/64487275-lg-luma` · Evaluated: 2026-11-13 · Evaluator: Arena agent (single execution agent)

Every claim below carries a classification. Nothing here is asserted from a summary,
a commit message, or an earlier report.

| Class | Meaning |
| --- | --- |
| PROVEN | Reproduced in this session with the command shown |
| MEASURED | Quantified by a command run in this session |
| OBSERVED | Read directly from a file, API response, or git object |
| INFERRED | Reasoned from evidence, not executed |
| PROPOSED | Recommendation, not implemented |
| BLOCKED | Could not be executed here, with the reason |
| NOT_RUN | Not attempted |

---

## 1. Source and target identities — PROVEN

Verified with `git ls-remote` and `gh api`, not assumed.

| Item | Claimed | Verified | Match |
| --- | --- | --- | --- |
| `lg-luma` `main` | `e5608cd0…` | `e5608cd053be5376a54a806129a332952dfabcef` | ✅ |
| Eval branch `lab/council-kit-snapshot-ff9a6b8-20261113` | `7fb8b953…` | `7fb8b953f4098bd0db836da343d39b2f1e9a9f3c` | ✅ |
| Source `luma-webos-launcher` `arena/5fe14abb-…` | `4debf5ed…` | `4debf5ed9eba06c0b71dca79b0c7f61aeacec112` (branch HEAD) | ✅ |
| PR #2 (integration) | draft | `DRAFT`, head `7fb8b953…` | ✅ |
| PR #1 (forensic audit) | draft | `DRAFT` | ✅ |

`4debf5e` commit subject: `fix: Rust test unwrap_err double-consumption + Aegis Rust coverage`,
dated `2026-11-13 10:28:24 +0000`.

### Toolkit copy is blob-exact — PROVEN

All 18 copied files were compared **by git blob SHA**, not by filename or size.

```
matched=18  differ=0
```

`aegis_bug_hunter.py` is `a79a9310728542a6ad98bcaeb069e2211a39f361` in both trees, so the
Aegis update *was* correctly propagated from `4debf5e`. `ADOPTION-NOTICE.md` is target-only.

Three source files were **not** copied (correctly — see §3):

* `COUNCIL_STARTER_KIT/.github/workflows/council.yml`
* `COUNCIL_STARTER_KIT/.pre-commit-config.yaml`
* `COUNCIL_STARTER_KIT/docs/xray/_data/execution_receipts.json`

### Pins re-verified against the live remotes — PROVEN

Re-checked with `git ls-remote` after the analysis was complete, in case either repository
had moved:

| Ref | Value | Changed? |
| --- | --- | --- |
| source `arena/5fe14abb-…` | `4debf5ed9eba06c0b71dca79b0c7f61aeacec112` | no |
| source `main` | `40994fc144b5af481056d14e2fb93304aa1e2c82` | no |
| target `lab/council-kit-snapshot-ff9a6b8-20261113` | `7fb8b953f4098bd0db836da343d39b2f1e9a9f3c` | no |
| target `main` | `e5608cd053be5376a54a806129a332952dfabcef` | no |

Source `main` is not an alternative source of the toolkit: it contains **no
`COUNCIL_STARTER_KIT/` directory at all** (`git ls-tree … | wc -l` → 0), its last commit is
`40994fc1` *"README: link the case study"* (2026-10-27), and it sits **64 commits behind**
`arena/5fe14abb-…` with 0 commits of its own (`rev-list --left-right --count` → `0  64`).
`4debf5e` is therefore the latest version of the toolkit anywhere in that repository.

Blob-exactness was also re-verified a second time by an independent method — `git hash-object`
on the working-tree files rather than comparing `ls-tree` output:

```
blob-exact=18  mismatched=0
```

---

## 2. Two corrections to the brief's premises

### 2a. `lg-luma` CI has never executed — OBSERVED

The brief says to "reuse this pipeline" and to "determine whether the active PR already
triggers relevant CI jobs". Measured:

```
gh api repos/SteveSpivak/lg-luma/actions/runs      -> total_count = 0
gh api repos/SteveSpivak/lg-luma/actions/workflows -> total_count = 0
gh pr checks 2  -> "no checks reported on the 'lab/council-kit-snapshot-ff9a6b8-20261113' branch"
gh pr checks 1  -> "no checks reported on the 'research/council-kit-adoption-audit-20261112' branch"
```

`.github/workflows/ci.yml` has been tracked since `e5608cd` (2026-10-31), yet GitHub
registers **zero** workflows and **zero** runs.

The same API call against the **source** repository returns three active workflows, so the
endpoint itself works and the difference is repo-specific:

```
lg-luma              actions/workflows -> total_count = 0
luma-webos-launcher  actions/workflows -> total_count = 3
    CI                              state=active  .github/workflows/ci.yml
    Arena offline lab validation    state=active  .github/workflows/arena-lab.yml
    Agent evidence contract         state=active  .github/workflows/agent-evidence.yml
```

A controlled experiment settled it. A commit was pushed to this branch with PR #3 open, which
satisfies the `on: pull_request` trigger in `ci.yml`. Result: no workflow run was created
(see §2c). GitHub Actions is therefore **disabled** for `lg-luma` — upgraded from INFERRED
to PROVEN by experiment.

Consequence: **no CI evidence exists for PR #1 or PR #2**, and "reuse the pipeline" cannot
produce results until Actions is enabled. This is the single largest blocker in the task.

### 2b. The Rust test commands in the brief cannot run in `lg-luma` — PROVEN

`grep -rn nuvio Cargo.toml` in `lg-luma` returns nothing. The `nuvio` and `nuvio_lab`
features exist only in the source launcher's manifest:

```toml
# luma-webos-launcher/Cargo.toml
nuvio = []
nuvio_lab = []
```

`lg-luma` declares only `default = []` and `webos`. Therefore
`cargo test --locked --features nuvio` and `--features nuvio,nuvio_lab` are **not
meaningful in `lg-luma`**; they belong to the source repository. The brief's own caveat on
this point is confirmed.

### 2c. CI archaeology: `cargo test` has never run against the Nuvio code — PROVEN

`lg-luma` is not the only repository without Rust test evidence. The source repository has
run CI 56 times, and the history was reconstructed from the jobs API:

```
total=56  success=1  failure=37  cancelled=18        (workflow "CI", id 408422528)
runs on branch main: 0
```

**Every one of the 37 failures dies at the same step.** Sampled across 8 runs spanning two
branches (`arena/5fe14abb-…` and `governance/agent-evidence-contract-…`):

```
42296159711  failed=[…@Check formatting]  unit_tests_conclusion=[skipped]
42295299623  failed=[…@Check formatting]  unit_tests_conclusion=[skipped]
42291963017  failed=[…@Check formatting]  unit_tests_conclusion=[skipped]
42215076698  failed=[…@Check formatting]  unit_tests_conclusion=[skipped]
42214266561  failed=[…@Check formatting]  unit_tests_conclusion=[skipped]
42197140917  failed=[…@Check formatting]  unit_tests_conclusion=[skipped]
42189981711  failed=[…@Check formatting]  unit_tests_conclusion=[skipped]
42212559998  failed=[…@Check formatting]  unit_tests_conclusion=[skipped]
```

`Check formatting` is `pnpm format:check` = `cargo fmt --all -- --check && oxfmt --check .`.
Because it fails, `Run unit tests` is **skipped every time** — so `cargo test` never runs on
the branch that contains the Nuvio work and the toolkit.

The single success is not rescue either. Run `42134961928` (branch `arena/luma-phase1-tv`,
`10f81539`, `workflow_dispatch`, 2026-11-06T00:11Z) is fully green through
`Check formatting → Lint → Run unit tests → assets → rendering`. But that commit predates
the code under evaluation:

```
git show 10f81539:src/platform.rs | grep 'fn nuvio_app_id'   -> (no match)
git show 10f81539:src/tests.rs    | grep 'fails_closed'      -> (no match)
git show 10f81539:Cargo.toml  [features] -> default = [], nuvio = [], webos = [...]
                                          (no nuvio_lab)
```

Introducing commits, from `git log -S`:

| What | Commit | Date (UTC) |
| --- | --- | --- |
| `pub fn nuvio_app_id` | `f1d895b` | 2026-11-06 11:59:18 |
| `nuvio_app_id_lab_without_feature_fails_closed` | `ff9a6b8` | 2026-11-13 10:20:11 |
| only green `cargo test` run | `10f81539` | 2026-11-06 00:11:07 |

The green test run happened **11 h 48 min before `nuvio_app_id` existed** and **7 days before
its fail-closed test existed**. The newest CI run anywhere is `2026-11-06T21:22:14Z`
(`7c2e855d`), which is 7 days older than both `ff9a6b8` and `4debf5e`.

Conclusion: **`nuvio_app_id` and `nuvio_app_id_lab_without_feature_fails_closed` have never
been compiled or executed by any CI run in either repository.** This is independent of the
`cfg`-filtering problem in §8c — the test is excluded twice over: the code has never reached
a working `cargo test` at all, and the command that would run it (`--all-features`) filters
it out by its own gate.

Two further observations from the same history: the branch carries commit `a656c8c` *"fix:
resolve all 17 app + 49 test compile errors on PR head"*, and the one green run used a
*different* `ci.yml` (jobs `Rust checks and desktop rendering` / `Native webOS package`)
than the current one (`Rust checks, rendering, and native package`), so the pipeline was
restructured after its only green run.

CI job logs could not be retrieved to obtain the exact `rustfmt` diff: the API redirects to
`*.blob.core.windows.net` and `results-receiver.actions.githubusercontent.com`, neither of
which is reachable from this environment. The failing step name is PROVEN; the offending
lines are BLOCKED.

---

## 3. Component inventory and decisions

| Component | Purpose | Source blob | Dependencies | Side effects | Actual coverage | Gaps | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `nuvio_constraint_validator.py` | Stage 0 gate | `bb22b55d…` | none | none | tests its **own Python mirror** | never touches Rust | **ISOLATE** |
| `council_pipeline.py` | 8-stage orchestration | `62a2bdec…` | all tools, `git rev-parse` | writes `.agent-kb/*.json` | Stage 0 fail-fast is real | Stage 6 crashes without a manifest | **ADAPT** |
| `repo_sync.py` | drift detection | `c493fc3f…` | `scripts/repo_manifest.json` | writes receipts, `docs/xray/` | detects drift past 200 files | `return 0` unconditional | **ADAPT** |
| `aegis_bug_hunter.py` | bug scan | `a79a9310…` | stdlib only | writes `.agent-kb/hunt_cache.json` | 440/451 findings are noise | 2 regex defects + dead category | **REJECT (Rust rules)** |
| `tool_latent_codec.py` | output compression | `e33dd6b1…` | stdlib | writes handle store | 7.21x on real data, lossless | benchmark is synthetic | **ADAPT** |
| `nexus_agent_os.py` | index/checkpoint/bench | `ca0e8be0…` | `git` | `read-tree` + `checkout-index -f -a`, `shell=True` | sync/index work | destructive restore, worktree-unsafe | **ISOLATE** |
| `arena_guard.py` | receipts | `d2265a67…` | `git` | writes receipts | receipts issued correctly | — | **REUSE** |
| `council_entry.py` | CLI dispatcher | `41954b0d…` | all tools | — | dispatch works | wrong `REPO_ROOT` default | **ADAPT** |
| `tests/test_starter_kit.py` | self-test | `3de77035…` | all tools | runs them all | 8/9 pass here | step 8 fails in target layout | **ADAPT** |
| 9 `*.md` docs | documentation | various | — | none | — | paths say `scripts/…` | **ADAPT** |
| `.github/workflows/council.yml` | source CI | `69970093…` | GitHub | runs CI | not copied | would collide with `ci.yml` | **REJECT** |

### 3.1 What `lg-luma` already has, and what the toolkit duplicates — OBSERVED

Inventory of existing infrastructure on `main` at `e5608cd`:

* `tools/` — 16 build/packaging/asset scripts (`build-webos.sh`, `package.mjs`, `ipk.mjs`,
  `repository.mjs`, `release-gate.mjs`, `setup-webos-sdk.mjs`, `webos-runtime.mjs`,
  `sync-version.mjs`, asset generators)
* `tests/` — 11 suites: 4 Xvfb smoke suites plus `node --test` unit tests
* `pnpm` scripts wiring the real gates: `test` → `cargo test --workspace --all-features`,
  `check` → `oxlint` + `cargo clippy … -D warnings`, `format:check` → `cargo fmt --check`
  + `oxfmt --check`
* `oxlint` 1.88 + `oxfmt` 0.73 in devDependencies, with `.oxlintrc.json` setting
  `categories.correctness = "error"`
* `.github/workflows/` — `ci.yml` (job DAG `prepare → smoke|package → build → release`),
  `pr-test-ipk.yml`, `release-pr.yml`, `changeset-status.yml`
* `flake.nix` for a reproducible dev shell; `.changeset/` + changesets for versioning
* `agents.md`, `development.md` (79 KB), `assets.md` for agent instructions, plus an
  existing hash-pinned skill system (`.agents/skills/`, `skills-lock.json`)

| Toolkit capability | Already covered in `lg-luma` by | Verdict |
| --- | --- | --- |
| Stage orchestration / pipeline | `pnpm` scripts + the `ci.yml` job DAG | **REJECT** — a second orchestrator for a responsibility CI already owns |
| Rust bug detection | `cargo clippy … -D warnings` in `pnpm check` | **REJECT** (§7f) |
| TS/JS bug detection | `oxlint` with `correctness = error` in `pnpm check` | **REJECT** |
| Formatting | `cargo fmt --check` + `oxfmt --check` in `pnpm format:check` | **REJECT** |
| `nexus checkpoint` (save/restore) | `git stash`, `git worktree`, `git commit` | **REJECT** — reimplements git, and unsafely (§12) |
| `nexus bench` (timing/MAD) | `hyperfine`, or CI timings | **REJECT** |
| `repo_sync` cross-repo drift | nothing — but `lg-luma` is a single repository | **REJECT** — no cross-repo relationship exists here to drift against |
| `arena_guard` receipts | CI artifacts, `dist/sha256sums`, `tools/release-gate.mjs` | **ISOLATE** — overlapping provenance model |
| `nuvio_constraint_validator` | **17 real Rust tests** in `src/tests.rs` (source repo) | **REJECT as a substitute** (§5) |
| `tool_latent_codec` | nothing | **ADAPT** — genuinely novel, but see §9 |
| Agent instructions / handoff docs | `agents.md`, `development.md`, `.agents/skills/` | **REJECT** — duplicate, and would fork the instruction source of truth |
| `council.yml` workflow | `ci.yml` | **REJECT** — a parallel CI abstraction |

On that last Rust row, the real test suite is worth stating precisely. At `4debf5e`,
`mod nuvio` in the source repo contains **17 `#[test]` functions: 12 ungated and 5
`cfg`-gated**. The 5 gated ones split into disjoint sets:

| Requires | Tests |
| --- | --- |
| `all(nuvio, nuvio_lab)` | `nuvio_lab_app_id_is_distinct_and_valid`, `nuvio_app_id_production_returns_webos`, `nuvio_app_id_lab_returns_lab`, `nuvio_lab_launch_params_match_contract` |
| `all(nuvio, not(nuvio_lab))` | `nuvio_app_id_lab_without_feature_fails_closed` |

Because the two gates are mutually exclusive, **no single `cargo test` invocation covers all
17**. `--all-features` runs 16 and silently drops the fail-closed test; `--features nuvio`
runs 13 and drops the four lab tests. Full coverage needs both invocations, and neither
repository's CI runs either today (§2c). A Python mirror asserting against its own copy of
the logic does not close that gap.

---

## 4. The toolkit does not run green from its actual location — PROVEN

Run from the verified eval-branch worktree, exactly as shipped:

```
$ python3 lab/council-kit/tests/test_starter_kit.py
1..7  PASS   (parse, help, nexus sync, aegis hunt, dylib-audit, validate-constraints, cfg, bench-compression)
8. council pipeline full: FAIL rc=1, err=
SELF-TEST FAILED — 1 failure(s)
EXIT=1
```

This contradicts the `4debf5e` commit message ("All 9 self-test checks pass; full pipeline
completes in ~1.3s"). It is not a drift failure:

```
FileNotFoundError: [Errno 2] No such file or directory:
  '/home/user/eval-worktree/lab/council-kit/scripts/repo_manifest.json'
```

`repo_sync.py` hardcodes `MANIFEST_FILE = REPO_ROOT / "scripts" / "repo_manifest.json"`, and
no such file exists in `lg-luma` or in the copied toolkit. Stage 6 dies on an uncaught
exception; the receipt it would have written even hardcodes
`command="python3 scripts/repo_sync.py drift"` — a source-repo path.

### Path resolution is inconsistent across entry points — PROVEN

6 of 7 tools use `REPO_ROOT = Path(os.environ.get("REPO_ROOT", ".")).resolve()` — **CWD
dependent**. Only `council_entry.py` uses `KIT_DIR.parent`, which in the target layout
resolves to `lab/`, not the repo root:

```
KIT_DIR          = /home/user/eval-worktree/lab/council-kit
REPO_ROOT dflt   = /home/user/eval-worktree/lab      <- wrong
actual repo root = /home/user/eval-worktree
```

Confirmed by where the generated state actually landed after ordinary runs:

```
docs/xray/_data/execution_receipts.json          <- correct (REPO_ROOT set)
lab/docs/xray/_data/execution_receipts.json      <- wrong (council_entry default)
lab/.agent-kb/hunt_cache.json                    <- wrong (council_entry default)
lab/council-kit/docs/xray/_data/...              <- inside the TRACKED toolkit dir
lab/council-kit/.agent-kb/hunt_cache.json        <- inside the TRACKED toolkit dir
```

Generated evidence is written **inside tracked source directories**, which the brief
explicitly forbids. Fixing this requires a `REPO_ROOT` export in every documented
invocation, or anchoring all tools to a single discovery rule.

---

## 5. Stage 0 fail-fast — PROVEN (passes)

Controlled negative mutation in a separate worktree (`/home/user/mut-worktree`, detached at
`7fb8b953`), so `main`, the eval branch and this branch were never touched.

Mutation: make lab mode return the **production** app ID.

```python
if lab:
    if feature_nuvio_lab:
-       return NUVIO_LAB_APP_ID
+       return NUVIO_APP_ID  # MUTATION: unsafe fallback to production
```

Validator turns RED (`validator exit=1`), then:

```
[STAGE 0] nuvio_constraint_validator.py — constraint validation
  receipt=RCPT-D1C17DC8CA36 exit=1
[PIPELINE HALTED] Stage 0 constraint validation failed — not proceeding to subsequent stages.
COUNCIL PIPELINE HALTED — 70.39ms
  All stages passed: False
  Stages completed: 1
PIPELINE EXIT=1
```

| Required property | Result |
| --- | --- |
| Nonzero exit status | `PIPELINE EXIT=1` ✅ |
| Failure receipt | `RCPT-D1C17DC8CA36` ✅ |
| No later stages execute | `Stages completed: 1` ✅ |
| No shipping operation | Stage 7 not reached (also gated behind `--ship`) ✅ |
| No false PASS | `All stages passed: False` ✅ |
| Existing files intact | 19 files, all byte-identical except the mutated one ✅ |

Persisted receipt:

```json
{"all_passed": false, "halted_at": "stage_0_constraint_validation",
 "stages_completed": 1, "stages": [{"exit_code": 1, "receipt_id": "RCPT-D1C17DC8CA36"}]}
```

Restore verified byte-exact, then GREEN again:

```
git show 7fb8b95:lab/council-kit/nuvio_constraint_validator.py | sha256sum
  a48ed5b2ee7927381f80dc1bcb41efbe3edf40dce8c7915a238961dfd607a8b7
sha256sum lab/council-kit/nuvio_constraint_validator.py
  a48ed5b2ee7927381f80dc1bcb41efbe3edf40dce8c7915a238961dfd607a8b7
```

**Important limit:** Stage 0 is genuine fail-fast, but it is not evidence about the Rust
application. `nuvio_constraint_validator.py` defines its own Python `nuvio_app_id`,
`validate_nuvio_target` and `valid_app_id`, each commented "mirrored from src/platform.rs".
It asserts against the mirror. A bug in the real Rust `nuvio_app_id` would **not** fail
Stage 0. Treat Stage 0 as a regression test of the Python contract, never as validation of
`src/platform.rs`.

---

## 6. Drift: reporting vs enforcement — PROVEN

The brief asks whether `drift` still returns zero while reporting drift markers. **It does.**

```python
def cmd_drift(args):
    ...
    rcpt = issue_receipt("repo_sync_drift", "python3 scripts/repo_sync.py drift", 0, 0.0, report)
    report["receipt_id"] = rcpt
    print(json.dumps(report, indent=2))
    return 0            # <- unconditional
```

Test: supply a minimal manifest, then plant a real production app-ID marker past the old
200-file boundary (210 filler files first).

```
EXIT CODE = 0
"driftprobe/zz_deep_drift.rs:space.nuvio.webos"     <- detected
local_drift_markers categories: ['app_id_production', 'app_id_lab', 'feature_nuvio_lab',
  'stackitem_fields', 'renderer_iflet_guard', 'lckv_seqlock', 'launch_guard', 'ci_rust_toolchain']
```

Two separate conclusions:

1. **The 200-file limit is genuinely gone — PROVEN.** The planted file sits after 210
   filler files and was found. `detect_drift_locally()` uses unbounded `rglob`.
2. **It is still not a gate — PROVEN.** Exit 0 with 8 populated drift categories.
   `repo_sync.py drift` is informational. It must not be described as an invariant check.

Also MEASURED: `hits[:10]` caps each category at 10 reported entries, and the patterns are
very broad — `renderer_iflet_guard` matches any `if let`, `ci_rust_toolchain` matches the
word `toolchain`. On a Rust repo these generate large volumes of noise, including matches
inside the toolkit's own files.

---

## 7. Aegis Rust scanning — fixture-measured, and the heuristics fail

### 7a. Measured precision and recall

`lab/council-kit-eval/aegis_rust_eval.py` imports the **real** `scan_rs_file` /
`extract_rs_signatures_map` from the toolkit. Labels are content-anchored (no hardcoded line
numbers) and the harness aborts any label that does not match exactly one line.

Against the shipped toolkit at `7fb8b953`:

```
TP=4  FP=3  FN=5  TN=9
precision=0.571  recall=0.444  f1=0.500  FPR=0.250
```

| Declared category | Status |
| --- | --- |
| `TAUTOLOGICAL_COMPARISON_COPY_PASTE` | **DEAD — never fires** |
| `REDUNDANT_BOOLEAN_SUBEXPRESSION` | fires |
| `RS_UNWRAP_WITHOUT_OPTION_GUARD` | fires |

### 7b. Two concrete defects — PROVEN in isolation

**Defect 1 — the Rust tautology regex can never match a real tautology.**

```python
RS_TAUTOLOGY_RE = re.compile(r"==\s*(\w[\w.]*)\s*==\s*\1")
```

```
'a == a'              -> match=False
'a == b && b == b'    -> match=False
'a.len() == a.len()'  -> match=False
'== a == a'           -> match=True      # the only thing it matches
```

It requires **two** `==`. It was copied from `TSJS_TAUTOLOGY_RE` (`=== x === x`), where
chained strict equality is a real pattern. In Rust, `x == x` has one `==`. The category is
dead code.

**Defect 2 — a broken backreference disables every `x || x` check, in Rust *and* TS/JS.**

```python
RS_REDUNDANT_BOOL_RE   = re.compile(r"(\w[\w.]*)\s*&&\s*\1|(\w[\w.]*)\s*\|\|\s*\1")
TSJS_REDUNDANT_BOOL_RE = re.compile(r"(\w[\w.]*)\s*&&\s*\1|(\w[\w.]*)\s*\|\|\s*\1")
```

The second alternation binds group 2 but backreferences `\1`; an unmatched group makes `\1`
fail.

```
'a && a'           -> match=True
'a || a'           -> match=False     # TS/JS scanner has the same bug
'foo.bar || foo.bar' -> match=False
```

This is a **pre-existing** bug that the Rust addition inherited.

**Defect 3 — the guard rule treats every `.unwrap()` as suspicious.** `is_some()`/`is_none()`
is only consulted on the *same* line, so a guard on the previous line does not count, and
comments and `#[test]` bodies are flagged. `.expect()` — equally panicking — is not covered.

### 7c. False positives on the real `lg-luma` codebase — MEASURED

`src/` at baseline `e5608cd`, 44 Rust files:

```
total anomalies    : 451
   440  RS_UNWRAP_WITHOUT_OPTION_GUARD
    11  REDUNDANT_BOOLEAN_SUBEXPRESSION
```

**All 11 `REDUNDANT_BOOLEAN_SUBEXPRESSION` hits are false positives — 100%.** Every one is
the same single-character artefact:

```
src/sdl_events.rs:20   "if webos && scancode == 384 {"     -> MATCHED 's && s'
src/main.rs:597        "if !webos && std::path::Path..."   -> MATCHED 's && s'
src/view.rs:855        "if state.page == Page::Apps ..."   -> MATCHED 's && s'
```

`(\w[\w.]*)` matches a single `s`, so the last letter of the left operand and the first of
the right operand form a fake duplicate. Of the 440 unwrap warnings, **315 (71.6%)** are in
`*-tests.rs` files, where `.unwrap()` is idiomatic.

### 7d. Full-repository scan — MEASURED

§7c covered `src/` only. The whole repository is polyglot (Rust + JavaScript + Python), and
scanning all of it changes the picture:

```
$ REPO_ROOT=<repo> aegis_bug_hunter.py hunt --path .
exit 0 | wall 278.3 ms | peak child RSS 21.8 MB
files_scanned           : 65        (extensions: .js .jsx .py .rs .ts .tsx)
functions_modeled       : 1036
call_sites_cross_checked: 298
total_anomalies_found   : 684
anomalies listed        : 40        (rank_anomalies cap)
```

Uncapped, by category (670 from per-file scanning + 14 from cross-file call-arity analysis):

| Count | Category | Verified verdict |
| --- | --- | --- |
| 546 | `RS_UNWRAP_WITHOUT_OPTION_GUARD` | dominated by test files (§7c) |
| 111 | `TSJS_MISSING_OPTIONAL_CHAINING` | **false positives** |
| 14 | `CALL_ARITY_MISMATCH_TYPEERROR` | **14/14 false positives** |
| 13 | `REDUNDANT_BOOLEAN_SUBEXPRESSION` | **13/13 false positives** |

Seven of these come from this evaluation directory's own intentionally-defective fixtures, so
the repository-wide figure excluding them is 677.

**The call-arity check is broken by design, not by regex.** It builds one global
function-name map across all languages and matches call sites by bare name, so a Python or
JavaScript call is validated against an unrelated Rust function:

```
assets/tile-editor/app.js:L83          Calls 'focus()'   with 1 args, but src/state.rs:L744 requires [3..3].
lab/council-kit-eval/aegis_rust_eval.py:L94  Calls 'append()'  with 1 args, but src/scroll-preview.rs:L10 requires [3..3].
lab/council-kit-eval/aegis_rust_eval.py:L30  Calls 'resolve()' with 0 args, but tv-helper/src/files.rs:L14 requires [2..2].
tools/font-weights.py:L47              Calls 'replace()' with 2 args, but tv-helper/src/files.rs:L142 requires [3..3].
```

`list.append`, `str.replace`, `Path.resolve` and `element.focus` are compared against Rust
signatures that happen to share a name. On a polyglot repository this category cannot
produce a true positive, and it flagged this harness 11 times.

`TSJS_MISSING_OPTIONAL_CHAINING` is equally indiscriminate — it fires on ordinary, correct
JavaScript including an `import` statement:

```
assets/tile-editor/app.js:L1    import { checkListing, describe, loadListing, normalizeUrl, post } from './tiles.js';
assets/tile-editor/app.js:L136  event.preventDefault();
assets/tile-editor/app.js:L113  error.name === 'AbortError'
```

The 13 `REDUNDANT_BOOLEAN_SUBEXPRESSION` hits are all false positives: 11 are the
single-character `'s && s'` artefact from §7c, and the other 2 are
`control.rect.x && rect.x` / `control.rect.y && rect.y`, where the actual `&&` operands are
comparisons rather than bare identifiers.

Net: of the 27 findings in the two categories that can be checked exhaustively against real
code, **0 are true positives**. The 546 unwrap findings are not individually enumerated here,
but §7c measured 71.6% of them landing in test files.

### 7e. Fixture-only metrics are not sufficient — MEASURED

A minimal patch (word boundaries, `\2` backreference, single `==`, `expect()` coverage,
string/comment stripping, `#[test]` exclusion, 2-line window) reaches a perfect fixture
score:

```
TP=9  FP=0  FN=0  TN=12   precision=1.000  recall=1.000  FPR=0.000   -> harness PASS
```

But on the real codebase it is **worse**:

```
SHIPPED  total=451  {unwrap: 440, redundant: 11}
PATCHED  total=170  {unwrap: 64, TAUTOLOGY: 102, redundant: 4}
```

All 102 new tautology findings are false positives from closure parameters:

```
src/app_artwork.rs:453   "if let Some(index) = queue.background.iter().position(|r| r.token == token) {"
src/branding.rs:149      "BRANDS.iter().find(|brand| brand.key == key)"
src/main.rs:337          ".find(|a| a.id == id)"
```

`r.token == token` is not a tautology; the regex sees `token == token`. The 4 remaining
redundant-bool hits are likewise spurious (`… control.rect.x && rect.x < …`).

This is recorded as a **verification result, not a success**: the patch was tuned to the
fixture set and overfit. Regex/line matching cannot distinguish `x == x` from
`a.x == x` or from a comparison inside a closure. Only real parsing can.

### 7f. Decision — REJECT the Rust rules, REUSE Clippy

`lg-luma` already enforces Clippy with warnings as errors:

```
"check": "... && cargo clippy --locked --workspace --all-targets --all-features -- -D warnings"
```

INFERRED (not executed here — see §8): Clippy's `eq_op` (correctness group, deny-by-default)
covers `x == x`, and `nonminimal_bool` (style group, warn-by-default) covers `a && a` /
`a || a`. Both operate on the real AST, so neither produces the artefacts above, and both
are **already wired into `pnpm check`**. `.unwrap()`/`.expect()` policy is available via the
opt-in restriction lints `clippy::unwrap_used` and `clippy::expect_used`, which let the
project scope the rule (for example `tests/**` exempt) instead of accepting 440 warnings.

So the Rust portion of Aegis duplicates tooling this repository already runs, at lower
accuracy. Keep Aegis for Python/TS/JS; do not adopt its Rust rules.

---

## 8. Rust feature-matrix verification — BLOCKED locally, with a structural finding

### 8a. What could not run, and exactly why

```
rustc: command not found      cargo: command not found      rustup: command not found
pkg-config: command not found (SDL2 absent)                 pnpm: command not found
Xvfb: not installed           pytest: not installed
```

Installation was attempted, not assumed impossible:

```
static.rust-lang.org -> 000     crates.io -> 000     index.crates.io -> 000
deb.debian.org       -> 000     registry.npmjs.org -> 200     pypi.org -> 200
```

`rustup` is unreachable **and** `crates.io` is unreachable, so even a hand-installed
compiler could not fetch dependencies. `apt-get` exists but has no reachable mirror.
Therefore `cargo fmt/check/test/clippy` are **BLOCKED** in this sandbox, for both
repositories. No Python substitute was offered in their place.

### 8b. The source implementation was re-read, not trusted — OBSERVED

`src/platform.rs` at `4debf5e`:

```rust
pub fn nuvio_app_id(lab: bool) -> Result<&'static str, String> {
    if lab {
        #[cfg(feature = "nuvio_lab")]
        { return Ok(NUVIO_LAB_APP_ID); }
        #[cfg(not(feature = "nuvio_lab"))]
        { return Err("nuvio_app_id: lab=True but nuvio_lab feature not enabled — \
             refusing to silently fall back to production app ID \
             (space.nuvio.webos)".to_owned()); }
    }
    Ok(NUVIO_APP_ID)
}
```

Fail-closed is real. `git show 4debf5e -- src/tests.rs` confirms the `unwrap_err()`
double-consumption was replaced by `expect_err()` plus a captured `error` string. Both
claims in the brief hold as source facts.

### 8c. The safety test is structurally excluded from CI — PROVEN by inspection

The test's own gate:

```rust
#[cfg(all(feature = "nuvio", not(feature = "nuvio_lab")))]
#[test]
fn nuvio_app_id_lab_without_feature_fails_closed() { … }
```

The three positive tests use the opposite gate,
`#[cfg(all(feature = "nuvio", feature = "nuvio_lab"))]`. The source repository's only CI
job runs:

```
"test": "pnpm test:release && pnpm test:home && pnpm test:icons && cargo test --locked --workspace --all-features"
```

`--all-features` enables `nuvio_lab`, so `not(feature = "nuvio_lab")` is false and
**`nuvio_app_id_lab_without_feature_fails_closed` is never compiled, never run, by any CI
job in either repository.** The property "missing lab feature cannot silently launch
production" is asserted only by a test that no pipeline executes. The cfg semantics are
unambiguous; the execution that would confirm it is BLOCKED (§8a).

This is the most consequential finding in the task, and it is independent of the toolkit.

### 8d. Also PROVEN: no CI has validated the current source HEAD

The last CI run on `arena/5fe14abb-…` is `42296159711`, `conclusion=failure`,
`head_sha=7c2e855d4680b917432f66074fb552035b6e02a9`, created `2026-11-06T21:22:14Z`. The
branch HEAD is `4debf5e…` (`2026-11-13T10:28:24Z`). So `4debf5e` — the commit containing the
test fix — has **never** been through CI, and neither has `ff9a6b8`, the commit that
introduced the fail-closed test. Every run on that branch is `failure` or `cancelled`, and
all of them stop at `cargo fmt --check`. See §2c for the full reconstruction.

### 8e. The Rust mutation test — NOT_RUN

The brief requires restoring the unsafe Rust fallback in an isolated worktree and watching
the test go RED. This needs `cargo`; it is **NOT_RUN**, blocked by §8a. It must be run in
GitHub Actions on the **source** repository, with both feature sets, e.g.:

```
cargo test --locked --features nuvio                 # fail-closed test must run
cargo test --locked --features nuvio,nuvio_lab       # three positive tests must run
cargo test --locked --all-features                   # fail-closed test is FILTERED OUT
```

---

## 9. Codec measurement — MEASURED

### 9a. The shipped benchmark is self-referential

`bench-compression` reports `token_compression_ratio_x = 653.53` and
`root_cause_exact_coordinate_recall_pct = 100.0`. Reading the implementation:

```python
def cmd_bench_compression(args):
    """Synthesize a realistic 5,255-error pytest collection log …"""
    for i in range(5255):
        err_msg, root_coord = root_causes[i % len(root_causes)]
```

It generates 4 root causes repeated in a strict `i % 4` cycle, then measures recall against
`root_causes` — the same list it just used to build the input. `4/4` and `100%` are
tautological. This is the best possible case for deduplication and is not evidence about
real logs.

### 9b. Real command, real data

```
$ tool_latent_codec.py run -- aegis_bug_hunter.py hunt --path src
⚡ [LATENT COMPRESSION] 2489 raw tokens -> 345 latent-digest tokens (7.21x compression)
```

**7.21x**, not 653x — roughly 90x less than the synthetic figure.

The `deref` round-trip genuinely works:

```
$ tool_latent_codec.py deref @H-552FEFBC --lines 1:12
L10    |       "category": "REDUNDANT_BOOLEAN_SUBEXPRESSION",
L11    |       "location": "src/main.rs:L597",
```

So "lossless" holds **for what was captured**. But the upstream tool had already discarded
most of the evidence:

```
aegis total_anomalies_found = 451
aegis anomalies emitted     = 40     (8.9%)
locations recoverable via deref = 40
```

`rank_anomalies` truncates to 40 before the codec ever runs, so 411 findings (91.1%) are
unrecoverable by any amount of dereferencing. The compression ratio is therefore partly an
artefact of upstream truncation. Note also that the frame's "high-surprisal salient lines"
are dominated by JSON boilerplate (`{`, `},`, `"severity": "HIGH"`) rather than findings,
and the coordinate summary collapses line numbers (`src/app-artwork-tests.rs:(x29)`).

No intelligence or efficiency gain is claimed from this. The measured facts are: 7.21x on
real data, lossless within the captured payload, and a 91.1% upstream evidence loss that the
codec neither causes nor repairs.

### 9c. CLI ergonomics — OBSERVED

The frame prints `DEREF: tool_latent_codec.py deref @H-B945FCE2`, but `--lines` requires
`start:end` and the filter flag is `--grep`, not `--regex`. Both were hit by first-try
invocations:

```
ERROR: --lines must be start:end (e.g. 10:30)      exit=2
error: unrecognized arguments: --regex location
```

`--path` outside `REPO_ROOT` raises an uncaught `ValueError` from `relative_to()` rather than
a clear message.

---

## 10. Performance baseline — MEASURED

`aegis hunt --path src` against the real 44-file `src/` tree, `REPO_ROOT=/home/user/lg-luma`:

| Metric | `hunt --path src` | `hunt --path .` (full repo) |
| --- | --- | --- |
| exit code | 0 | 0 |
| wall time | 286.1 ms | 278.3 ms |
| peak child RSS | 21.2 MB | 21.8 MB |
| files scanned | 44 | 65 |
| findings computed | 451 | 684 |
| findings emitted | 40 | 40 |
| functions modelled | — | 1036 |
| call sites cross-checked | — | 298 |

Full pipeline (Stage 0→6, excluding the crashing Stage 6): ~1.0 s. Scanning is cheap; the
problem is signal, not cost — 684 findings of which 0 in the exhaustively checkable
categories are true (§7d). Note the fixed 40-finding output cap: at full-repo scale the tool
computes 684 and surfaces 40, so 94.2% of its own output is discarded before any consumer
sees it.

These are baselines for regression comparison; no candidate change to the application was
made, so no baseline-vs-candidate comparison applies.

---

## 11. Regression status

| Suite | Result | Reason |
| --- | --- | --- |
| `cargo test --locked --workspace --all-features` | **BLOCKED** | no toolchain, `crates.io` unreachable |
| `cargo clippy … -D warnings` | **BLOCKED** | same |
| `cargo fmt --all -- --check` | **BLOCKED** | same |
| `pnpm install --frozen-lockfile` / `check` / `test` | **NOT_RUN** | no `pnpm`; requires cargo underneath |
| Desktop smoke suites under Xvfb | **NOT_RUN** | no Xvfb, no SDL2 |
| ARMv7 cross-build + IPK packaging | **NOT_RUN** | requires the webOS SDK and network |
| `lab/council-kit/tests/test_starter_kit.py` | **FAIL 8/9** | missing `scripts/repo_manifest.json` |
| `lab/council-kit-eval/aegis_rust_eval.py` (new) | **FAIL (intended)** | documents §7 defects; exit 1 |

**No change was made to any file under `src/`, `tests/`, `tools/`, `Cargo.toml`,
`package.json` or `.github/`.** Existing `lg-luma` functionality cannot regress from this
branch because nothing it builds or runs was touched. The only additions are new files under
`lab/council-kit-eval/`.

---

## 12. Safety boundaries — respected

No TV contact of any kind. Specifically NOT_RUN: IPK install or launch, TV setting changes,
playback triggers, production Nuvio launch, app-ID replacement, account/profile changes,
root operations, production deploys.

`nexus_agent_os.py` was **not** executed in any repository containing uncommitted work.
OBSERVED risk, from source: `checkpoint restore` runs `git read-tree <tree>` followed by
`git checkout-index -f -a`, and `run_timed_sample` uses `subprocess.run(cmd_str, shell=True)`.
It also assumes `REPO_ROOT/.git/index` is a file, which is false in a linked worktree (there
`.git` is a gitdir pointer), so `checkpoint save` would copy the pointer text as an index.
All mutation work was confined to a throwaway detached worktree.

No credentials, tokens, or device data were written into any receipt.

---

## 13. Files changed on this branch

All additions; nothing existing modified.

```
lab/council-kit-eval/README.md
lab/council-kit-eval/REPORT.md
lab/council-kit-eval/aegis_rust_eval.py
lab/council-kit-eval/verify_toolkit.sh
lab/council-kit-eval/fixtures/rust/LABELS.json
lab/council-kit-eval/fixtures/rust/tautology.rs
lab/council-kit-eval/fixtures/rust/redundant.rs
lab/council-kit-eval/fixtures/rust/unwraps.rs
lab/council-kit-eval/fixtures/rust/sigs.rs
```

Rollback: `git rm -r lab/council-kit-eval` — the directory is self-contained, imports
nothing at runtime except the toolkit it evaluates, and no build, test, CI or packaging path
references it. PR #2's `lab/council-kit/` is untouched by this branch.

---

## 14. Recommendation — **HOLD**

Do not merge PR #2 for active integration. The toolkit is a reasonable research artefact and
its Stage 0 gate is genuinely fail-fast, but four findings block adoption:

1. **It does not run from its actual location.** The shipped self-test fails 8/9 on a
   missing `scripts/repo_manifest.json`, and generated evidence lands inside tracked
   directories. (§4)
2. **`drift` is not a gate.** Unconditional `return 0` with 8 populated drift categories.
   It must never be presented as enforcement. (§6)
3. **The Rust heuristics are unsound, and so are the cross-language ones.** One dead
   category, a broken backreference, and on a full-repository scan 684 findings of which
   **0 are true positives** in the 27 that can be checked exhaustively: the call-arity check
   matches calls by bare name across languages, so Python's `append()` is validated against a
   Rust `append` in `src/scroll-preview.rs`. Meanwhile `pnpm check` already runs Clippy and
   oxlint with `-D warnings`. (§7, §7d)
4. **No CI exists to validate any of it.** Zero workflow runs in `lg-luma` with Actions
   provably disabled, and in the source repository all 37 CI failures stop at
   `cargo fmt --check` with unit tests skipped — so the Nuvio code and its fail-closed test
   have never been compiled anywhere. (§2a, §2c, §8c, §8d)

### Minimum conditions to move HOLD → ready

* Add `scripts/repo_manifest.json` (or make `load_manifest()` degrade gracefully) and
  re-run `test_starter_kit.py` to 9/9.
* Anchor `REPO_ROOT` identically in all seven tools; redirect `.agent-kb/` and
  `docs/xray/` out of tracked directories; add them to `.gitignore`.
* Make `drift` return nonzero on findings, or split it into `drift-report` (exit 0) and
  `drift-check` (exit 1). Keep the receipt's `exit_code`/`duration_ms` truthful.
* Drop `RS_TAUTOLOGY_RE` / `RS_REDUNDANT_BOOL_RE` / the unwrap heuristic in favour of
  Clippy; fix the `\1`→`\2` backreference in `TSJS_REDUNDANT_BOOL_RE` regardless, since it
  affects the pre-existing TS/JS scanner.
* Enable GitHub Actions on `lg-luma` and confirm at least one green run of `ci.yml`.
* In the **source** repository, fix the persistent `cargo fmt --all -- --check` failure that
  has blocked all 37 CI runs. Until `Check formatting` passes, `Run unit tests` is skipped
  and no Rust claim about that branch can be validated by CI at all.
* In the **source** repository, add a CI job running `cargo test --features nuvio` so
  `nuvio_app_id_lab_without_feature_fails_closed` actually executes, and run the Rust
  mutation test there. (§8c, §8e)

---

## 15. Claim register

| Claim | Class |
| --- | --- |
| All repository/branch/PR SHAs match the brief | PROVEN |
| 18/18 copied toolkit files are blob-exact with `4debf5e` | PROVEN |
| Aegis was correctly updated from `4debf5e` | PROVEN |
| Toolkit self-test fails 8/9 in the target layout | PROVEN |
| Cause is a missing `scripts/repo_manifest.json`, not drift | PROVEN |
| Stage 0 halts on failure, writes a receipt, runs nothing later | PROVEN |
| Restore is byte-exact and returns Stage 0 to GREEN | PROVEN |
| `drift` detects markers past 200 files | PROVEN |
| `drift` still exits 0 while reporting drift | PROVEN |
| Stage 0 validates a Python mirror, not `src/platform.rs` | OBSERVED |
| `nuvio_app_id` fails closed in source | OBSERVED |
| `expect_err()` replaced `unwrap_err()` in `4debf5e` | PROVEN (git diff) |
| Fail-closed test is excluded by `--all-features` in CI | PROVEN by inspection |
| `lg-luma` has zero CI runs and zero registered workflows | OBSERVED |
| GitHub Actions is disabled in `lg-luma` (source repo shows 3 active workflows; a push with an open PR created no run) | PROVEN |
| Source CI: 56 runs, 1 success, 37 failures, 18 cancelled, 0 on `main` | PROVEN |
| All 37 source CI failures stop at `cargo fmt --check`; unit tests always skipped | PROVEN |
| The 1 green run predates `nuvio_app_id` by 11 h 48 m and the fail-closed test by 7 days | PROVEN |
| `nuvio_app_id` + its fail-closed test have never been compiled by any CI in either repo | PROVEN |
| `mod nuvio` holds 17 tests: 12 ungated, 5 `cfg`-gated in two mutually exclusive sets | PROVEN |
| No single `cargo test` invocation covers all 17 | PROVEN by inspection |
| `lg-luma` already wires clippy, oxlint, oxfmt and rustfmt into `pnpm check` / `format:check` | OBSERVED |
| All pins unchanged on re-check against the live remotes | PROVEN |
| Source `main` contains no toolkit and is 64 commits behind the arena branch | PROVEN |
| Blob-exactness re-confirmed by a second method (`git hash-object`): 18/18, 0 mismatched | PROVEN |
| Full-repo scan: 65 files, 684 findings, 278 ms, 21.8 MB peak RSS | MEASURED |
| `CALL_ARITY_MISMATCH_TYPEERROR` is 14/14 false positive (cross-language name matching) | MEASURED |
| `TSJS_MISSING_OPTIONAL_CHAINING` fires on `import` statements and `event.preventDefault()` | MEASURED |
| `REDUNDANT_BOOLEAN_SUBEXPRESSION` is 13/13 false positive repo-wide | MEASURED |
| 0 true positives across the 27 exhaustively checkable findings | MEASURED |
| Exact `rustfmt` diff from CI logs | BLOCKED (logs on unreachable hosts) |
| Aegis Rust precision 0.571 / recall 0.444 on labelled fixtures | MEASURED |
| Tautology category is dead code | PROVEN |
| `\|\|` backreference bug also affects the TS/JS scanner | PROVEN |
| 11/11 boolean findings on real code are false positives | MEASURED |
| 315/440 unwrap findings are in test files | MEASURED |
| Patched rules score 1.000 on fixtures but add 102 real false positives | MEASURED |
| Codec achieves 7.21x on real data; 653x is synthetic | MEASURED |
| 91.1% of findings are lost upstream of the codec | MEASURED |
| Aegis hunt: 286 ms, 21.2 MB peak RSS, 44 files | MEASURED |
| Clippy `eq_op` / `nonminimal_bool` cover these cases | INFERRED (not executed) |
| `cargo fmt/check/test/clippy`, `pnpm *`, Xvfb smoke, ARM/IPK | BLOCKED / NOT_RUN |
| Rust mutation test (restore unsafe fallback, expect RED) | NOT_RUN |
| Any TV or production operation | NOT_RUN (out of scope) |
