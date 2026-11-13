# Council Toolkit Evaluation (`lab/council-kit-eval/`)

Independent verification of the Council starter kit copied into `lg-luma` at
`lab/council-kit/` (branch `lab/council-kit-snapshot-ff9a6b8-20261113`, PR #2).

**Read [`REPORT.md`](REPORT.md) for findings.** This directory holds the evidence
that report cites, in a form you can re-run.

## Why this directory exists

The toolkit was copied into `lg-luma` with a claim of "all 9 self-test checks pass".
That claim does not hold in this repository, and several of the toolkit's Rust
heuristics are provably unsound. Rather than assert that, this directory reproduces
each finding deterministically.

## What is here

| File | Purpose |
| --- | --- |
| `REPORT.md` | The durable research report, with every claim classified |
| `verify_toolkit.sh` | End-to-end verification: location, self-test, Stage 0 mutation, drift, Aegis, toolchain |
| `aegis_rust_eval.py` | Precision/recall of `scan_rs_file` against labelled Rust fixtures |
| `fixtures/rust/*.rs` | Labelled Rust fixtures (tautologies, redundant booleans, unwraps, signatures) |
| `fixtures/rust/LABELS.json` | Ground truth, content-anchored so line numbers cannot drift |

Nothing here is imported by any build, test, CI or packaging path. `git rm -r
lab/council-kit-eval` is the complete rollback.

## Running it

The toolkit under test lives on PR #2's branch, not on `main`. Point `COUNCIL_KIT`
at a checkout of it:

```bash
git fetch origin lab/council-kit-snapshot-ff9a6b8-20261113
git worktree add --detach /tmp/council-kit \
    origin/lab/council-kit-snapshot-ff9a6b8-20261113

COUNCIL_KIT=/tmp/council-kit/lab/council-kit lab/council-kit-eval/verify_toolkit.sh
```

Once PR #2 is merged, `COUNCIL_KIT` defaults to `lab/council-kit` and no flag is needed.

Individual pieces:

```bash
# Precision / recall of the toolkit's real Rust scanner
COUNCIL_KIT=/tmp/council-kit/lab/council-kit \
    python3 lab/council-kit-eval/aegis_rust_eval.py
```

## Expected results today

`verify_toolkit.sh` exits **1**, and that is the correct outcome — it is reporting real
defects, not a broken harness:

| Check | Expected | Why |
| --- | --- | --- |
| 1. toolkit location | PASS | — |
| 2. shipped self-test | **FAIL** | `scripts/repo_manifest.json` does not exist in `lg-luma` |
| 3. Stage 0 fail-fast | PASS | mutation halts the pipeline; restore returns it to green |
| 4. drift as a gate | **FAIL** | `repo_sync.py drift` returns 0 while reporting drift |
| 5. Aegis Rust quality | **FAIL** | precision 0.571 / recall 0.444; one category never fires |
| 6. Rust / webOS | BLOCKED | no toolchain in this sandbox |

`aegis_rust_eval.py` likewise exits 1 against the shipped toolkit by design: its
thresholds (`MIN_PRECISION=0.90`, `MIN_RECALL=0.80`) sit **above** the measured baseline
so the harness fails until the defects in REPORT.md §7 are fixed. Both thresholds are
overridable:

```bash
MIN_PRECISION=0.5 MIN_RECALL=0.4 COUNCIL_KIT=... python3 lab/council-kit-eval/aegis_rust_eval.py
```

Relaxing the thresholds only silences the two numeric checks. The harness still exits 1
against the shipped toolkit, because two checks are not threshold-based and remain real
failures: the `TAUTOLOGICAL_COMPARISON_COPY_PASTE` category never fires, and
`extract_rs_signatures_map` mis-extracts arguments for `snake_case_params`, `mixed` and
`with_self`.

## Method notes

* `aegis_rust_eval.py` **imports** `scan_rs_file` and `extract_rs_signatures_map` from the
  toolkit on disk. It does not re-implement, copy or mirror them, so the numbers move when
  the toolkit changes.
* Labels are anchored to a unique substring of each fixture line, never to a hardcoded line
  number. A label that does not match exactly one line is reported and excluded.
* The harness was proven **satisfiable**: a patched copy of the scanner reaches
  `precision=1.000 recall=1.000 FPR=0.000` on these fixtures. A gate that could not go
  green would prove nothing. REPORT.md §7d records that the same patch then *degrades*
  precision on real code, which is itself a finding.
* The Stage 0 mutation test runs in a throwaway `git worktree` that the script removes on
  exit. `main`, the evaluation branch and this branch are never modified.

## Scope boundaries

No TV contact. No IPK install or launch, no TV setting changes, no playback, no production
Nuvio launch, no app-ID replacement, no account or profile changes, no root operations, no
production deploys. `nexus_agent_os.py` is never executed against a repository containing
uncommitted work, because its `checkpoint restore` path runs `git read-tree` followed by
`git checkout-index -f -a`.
