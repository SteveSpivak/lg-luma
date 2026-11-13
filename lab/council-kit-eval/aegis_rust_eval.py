#!/usr/bin/env python3
"""Precision / recall harness for the Council toolkit's Aegis Rust scanner.

This imports the REAL `scan_rs_file` and `extract_rs_signatures_map` from the
toolkit at its actual location in this repository (`lab/council-kit/`). It does
not re-implement, copy or mirror any of the logic under test: if the toolkit's
heuristics change, these numbers change.

Ground truth lives in `fixtures/rust/LABELS.json`. Every label is anchored to a
unique substring of the fixture line rather than a hardcoded line number, and
the harness aborts a label that does not match exactly one line.

Usage:
    python3 lab/council-kit-eval/aegis_rust_eval.py
    COUNCIL_KIT=/path/to/lab/council-kit python3 lab/council-kit-eval/aegis_rust_eval.py

Exit code is 0 only when the scanner reaches the quality thresholds below; a
regression in precision or recall therefore fails the harness rather than being
buried in a printed table.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = Path(os.environ.get("REPO_ROOT", HERE.parents[1])).resolve()
KIT = Path(os.environ.get("COUNCIL_KIT", REPO_ROOT / "lab" / "council-kit")).resolve()
FIXTURES = Path(os.environ.get("FIXTURES", HERE / "fixtures" / "rust")).resolve()

# Acceptance thresholds. These were set from the measured 2026-11-13 baseline
# (precision 0.571 / recall 0.444) and deliberately sit ABOVE it: the harness is
# intended to fail until the two regex defects documented in REPORT.md are fixed.
MIN_PRECISION = float(os.environ.get("MIN_PRECISION", "0.90"))
MIN_RECALL = float(os.environ.get("MIN_RECALL", "0.80"))


def load_kit():
    """Import the toolkit module under test from its real on-disk location."""
    target = KIT / "aegis_bug_hunter.py"
    if not target.exists():
        sys.exit(
            f"ERROR: toolkit not found at {target}\n"
            "The Council toolkit lives on branch "
            "`lab/council-kit-snapshot-ff9a6b8-20261113` (PR #2). Check it out, or "
            "point COUNCIL_KIT at a directory containing aegis_bug_hunter.py."
        )
    spec = importlib.util.spec_from_file_location("aegis_under_test", target)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    aegis = load_kit()
    labels = json.loads((FIXTURES / "LABELS.json").read_text())

    found: dict[tuple[str, int], set[str]] = {}
    for path in sorted(FIXTURES.glob("*.rs")):
        result = aegis.scan_rs_file(path.name, path.read_text())
        for anomaly in result["anomalies"]:
            line_no = int(anomaly["location"].split(":L")[1])
            found.setdefault((path.name, line_no), set()).add(anomaly["category"])

    tp = fp = fn = tn = 0
    skipped = 0
    rows = []
    for fname, needle, expected, note in labels["anomaly_labels"]:
        lines = (FIXTURES / fname).read_text().splitlines()
        matches = [i for i, line in enumerate(lines, 1) if needle in line]
        if len(matches) != 1:
            print(f"!! LABEL ERROR {fname}: {needle!r} matched {len(matches)} lines")
            skipped += 1
            continue
        line_no = matches[0]
        hit = (fname, line_no) in found
        cats = ",".join(sorted(found.get((fname, line_no), ())))
        if expected and hit:
            verdict = "TP"
            tp += 1
        elif expected and not hit:
            verdict = "FN"
            fn += 1
        elif not expected and hit:
            verdict = "FP"
            fp += 1
        else:
            verdict = "TN"
            tn += 1
        rows.append((verdict, fname, line_no, note, cats))

    print(f"Aegis module : {KIT / 'aegis_bug_hunter.py'}")
    print(f"Fixtures     : {FIXTURES}")
    print()
    print(f"{'':3} {'file':15}{'L':>4}  {'note':44} {'categories'}")
    for verdict, fname, line_no, note, cats in rows:
        print(f"{verdict:3} {fname:15}{line_no:>4}  {note:44} {cats}")

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    fpr = fp / (fp + tn) if fp + tn else 0.0

    print(f"\nTP={tp} FP={fp} FN={fn} TN={tn} (labels skipped: {skipped})")
    print(
        f"precision={precision:.3f}  recall={recall:.3f}  "
        f"f1={f1:.3f}  FPR={fpr:.3f}"
    )

    print("\n=== declared category coverage on these fixtures ===")
    fired: set[str] = set()
    for path in sorted(FIXTURES.glob("*.rs")):
        for anomaly in aegis.scan_rs_file(path.name, path.read_text())["anomalies"]:
            fired.add(anomaly["category"])
    declared = {
        "TAUTOLOGICAL_COMPARISON_COPY_PASTE",
        "REDUNDANT_BOOLEAN_SUBEXPRESSION",
        "RS_UNWRAP_WITHOUT_OPTION_GUARD",
    }
    dead = []
    for category in sorted(declared):
        status = "FIRES" if category in fired else "DEAD "
        print(f"  {status} {category}")
        if category not in fired:
            dead.append(category)

    print("\n=== extract_rs_signatures_map argument extraction ===")
    sigs = aegis.extract_rs_signatures_map((FIXTURES / "sigs.rs").read_text())
    sig_failures = []
    for name, want in labels["signature_labels"].items():
        got = sorted(sigs.get(name, {}).get("required_args", []))
        ok = got == sorted(want)
        print(f"  {'OK ' if ok else 'BUG'} {name:20} expected={sorted(want)} got={got}")
        if not ok:
            sig_failures.append(name)

    print("\n=== verdict ===")
    problems = []
    if precision < MIN_PRECISION:
        problems.append(f"precision {precision:.3f} < required {MIN_PRECISION:.2f}")
    if recall < MIN_RECALL:
        problems.append(f"recall {recall:.3f} < required {MIN_RECALL:.2f}")
    if dead:
        problems.append(f"dead categories: {', '.join(dead)}")
    if sig_failures:
        problems.append(f"signature extraction wrong for: {', '.join(sig_failures)}")
    if skipped:
        problems.append(f"{skipped} ambiguous label(s) skipped")

    for problem in problems:
        print(f"  FAIL: {problem}")
    if not problems:
        print("  PASS: scanner meets the configured thresholds")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
