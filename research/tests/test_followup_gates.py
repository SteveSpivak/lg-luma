"""Regression contracts for follow-up tooling; no native or device execution."""
import hashlib
import json
import unittest
from pathlib import Path

from research.scripts.check_patch_integrity import validate_scope
from research.scripts.collect_receipts import compact_receipt
from research.scripts.make_candidate import candidate_patch

ROOT = Path(__file__).resolve().parents[2]
PATCH = ROOT / "delivery/patches/focus-depth.patch"
HANDOFF = "2a40c7bb3af080981653f975b5c1e983e4f78ef5"


class FollowupGates(unittest.TestCase):
    def test_generator_is_deterministic_and_matches_committed_artifact(self):
        self.assertEqual(candidate_patch(), PATCH.read_text())

    def test_new_file_metadata_regression(self):
        data = PATCH.read_bytes()
        self.assertEqual(set(validate_scope(data)), {"src/main.rs", "src/view.rs", "src/focus_experiment.rs"})
        malformed = data.replace(b"new file mode 100644\n", b"", 1)
        with self.assertRaisesRegex(ValueError, "creation metadata"):
            validate_scope(malformed)

    def test_integrity_receipt_has_both_directions_and_negative_controls(self):
        report = json.loads((ROOT / "research/audit/patch-integrity.json").read_text())
        self.assertTrue(report["all_passed"])
        self.assertTrue(report["forward_apply"] and report["reverse_apply"])
        self.assertTrue(report["scratch_outside_git_repository"])
        self.assertTrue(report["application_source_unchanged"])
        self.assertEqual(report["patch_sha256"], hashlib.sha256(PATCH.read_bytes()).hexdigest())
        self.assertEqual({s["name"]: s["exit_code"] for s in report["steps"]}, {
            "reverse_on_baseline_rejected": 1, "forward_check": 0, "forward_apply": 0,
            "double_apply_rejected": 1, "reverse_check": 0, "reverse_apply": 0,
            "stale_source_rejected": 1})

    def test_updated_handoff_is_the_current_pinned_snapshot(self):
        report = json.loads((ROOT / "research/audit/handoff-integrity.json").read_text())
        self.assertEqual(report["commit_sha"], HANDOFF)
        self.assertTrue(report["all_match"])
        self.assertEqual(report["file_count"], 18)
        self.assertFalse(report["untracked_extra_files"])

    def test_receipt_collector_preserves_runner_provenance(self):
        raw = {"schema": "luma-command-receipt/1", "label": "sample", "argv": ["node", "--test", "x.mjs"],
               "exit_code": 0, "execution_status": "PASS", "started_utc": "start", "finished_utc": "end",
               "duration_seconds": 0.125, "timed_out": False, "head": "a" * 40,
               "evidence_scope": "host command only",
               "outputs": {"sample.stdout.log": {"sha256": "b" * 64, "bytes": 3},
                           "sample.stderr.log": {"sha256": "c" * 64, "bytes": 0}}}
        result = compact_receipt(raw, "sample", "MEASURED_HOST", "test", "d" * 64)
        self.assertEqual(result["command_argv"], raw["argv"])
        self.assertEqual(result["head_sha"], raw["head"])
        self.assertEqual(result["duration_ms"], 125)
        self.assertEqual(result["stdout_sha256"], "b" * 64)
        self.assertEqual(result["stderr_bytes"], 0)
        with self.assertRaises(ValueError):
            compact_receipt({}, "sample", "OBSERVED", "", "d" * 64)


if __name__ == "__main__":
    unittest.main()
