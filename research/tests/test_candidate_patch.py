"""Static candidate/rollback contracts, NOT compilation or native behavior tests."""
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PATCH = ROOT / "delivery/patches/focus-depth.patch"

class CandidateContract(unittest.TestCase):
    def test_candidate_is_bounded_and_default_off(self):
        self.assertTrue(PATCH.is_file(), "Candidate patch has not been generated")
        text = PATCH.read_text()
        paths = subprocess.check_output(["git", "apply", "--numstat", str(PATCH)], cwd=ROOT, text=True)
        self.assertEqual({line.split('\t')[2] for line in paths.splitlines()},
                         {"src/main.rs", "src/view.rs", "src/focus_experiment.rs"})
        self.assertIn('pub fn from_environment(value: Option<&str>) -> bool', text)
        self.assertIn('value == Some("1")', text)
        self.assertIn('LUMA_FOCUS_DEPTH', text)
        self.assertIn('let shadow = crate::focus_experiment::card_shadow(', text)
        self.assertIn('out.shadow(rect, 19.2, shadow.blur, shadow.offset_y, shadow.alpha);', text)
        self.assertNotIn('Preferences', text)
        self.assertNotIn('diff --git a/tv/', text)
        self.assertNotIn('diff --git a/src/platform', text)

    def test_patch_applies_to_pinned_source_without_applying_it(self):
        self.assertTrue(PATCH.is_file())
        result = subprocess.run(["git", "apply", "--check", str(PATCH)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

if __name__ == "__main__":
    unittest.main()
