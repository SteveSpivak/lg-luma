import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "scripts"))
import reference_launcher as model

FACTS = json.loads((ROOT / "research/audit/reference-launcher-facts.json").read_text())
PIN = "40994fc144b5af481056d14e2fb93304aa1e2c82"


class PinTests(unittest.TestCase):
    def test_reference_is_pinned_and_licensed(self):
        reference = FACTS["reference"]
        self.assertEqual(reference["commit"], PIN)
        self.assertEqual(reference["full_name"], "funnymataleao/luma-webos-launcher")
        self.assertEqual(reference["license"], "MIT License")
        self.assertEqual(reference["tag"], "v2.2.160")
        self.assertEqual(reference["package_version"], reference["app_version"])
        self.assertEqual(reference["files_total"], 969)
        self.assertFalse(reference["commits_signed"])

    def test_our_tree_is_a_different_fork_not_a_superset_copy(self):
        ours = FACTS["ours"]
        self.assertEqual(ours["base"], "e5608cd053be5376a54a806129a332952dfabcef")
        # Blob counts must be relative to the audit base, never the moving branch tip.
        self.assertEqual(ours["compared_rev"], ours["base"])
        self.assertEqual(ours["app_id"], "com.ecklf.luma")
        self.assertEqual(FACTS["reference"]["app_id"], "com.denisefremov.luma")
        self.assertFalse(ours["shares_history_with_reference"])

    def test_experiment_is_independent_of_the_reference(self):
        self.assertTrue(FACTS["focus"]["independent_of_our_experiment"])


class BlobForensicsTests(unittest.TestCase):
    def test_shared_and_diverged_file_counts_are_consistent(self):
        blobs = FACTS["blobs"]
        self.assertEqual(blobs["common_paths"], 179)
        self.assertEqual(blobs["identical"], 126)
        self.assertEqual(blobs["changed"], blobs["common_paths"] - blobs["identical"])
        self.assertEqual(blobs["only_ours"], FACTS["ours"]["files_total"] - blobs["common_paths"])
        self.assertEqual(blobs["only_reference"], FACTS["reference"]["files_total"] - blobs["common_paths"])

    def test_areas_never_exceed_totals(self):
        for area, counts in FACTS["blobs"]["by_area"].items():
            self.assertLessEqual(counts["identical"], counts["common"], area)

    def test_module_inventory_matches_status(self):
        for module in FACTS["components"]:
            if module["status"] == "only_reference":
                self.assertIsNone(module["ours_lines"], module["path"])
                self.assertIsNone(module["delta_lines"], module["path"])
            elif module["status"] == "only_ours":
                self.assertIsNone(module["reference_lines"], module["path"])
            else:
                self.assertEqual(module["delta_lines"], module["reference_lines"] - module["ours_lines"], module["path"])


class FocusDesignTests(unittest.TestCase):
    def test_motion_constants_are_recorded(self):
        self.assertEqual(FACTS["focus"]["constants"]["FOCUS_IN"], 0.16)
        self.assertEqual(FACTS["focus"]["constants"]["FOCUS_OUT"], 0.16)
        self.assertEqual(FACTS["focus"]["constants"]["FOCUS_POP"], 0.55)
        self.assertEqual(FACTS["focus"]["constants"]["FOCUS_SHEEN"], 0.4)

    def test_shadow_calls_and_reduced_motion_are_counted(self):
        calls = FACTS["focus"]["shadow_calls"]
        self.assertEqual(calls["total"], calls["all_numeric_args"] + calls["interpolated"])
        self.assertGreater(calls["files"], 0)
        self.assertGreater(FACTS["focus"]["reduced_motion_total"], 0)
        self.assertTrue(FACTS["focus"]["apps_resting_skips_shadow"])

    def test_reference_spring_math_is_reproducible(self):
        spring = FACTS["perf_math"]["spring"]
        self.assertAlmostEqual(spring["peak_k"], model.pop_peak_k(), places=9)
        self.assertAlmostEqual(spring["peak"], model.pop_peak(), places=9)
        self.assertAlmostEqual(spring["equivalent_damping"], model.equivalent_damping(model.pop_peak() - 1), places=9)
        self.assertAlmostEqual(spring["zoom_at_peak"], 1 + 0.07 * model.pop_peak(), places=9)


class PerfModelTests(unittest.TestCase):
    def test_shadow_areas_are_reproducible_from_constants(self):
        areas = FACTS["perf_math"]["shadow_area_px"]
        self.assertAlmostEqual(areas["ours_resting_blur22"], model.shadow_quad(model.CARD_W, model.CARD_H, 22))
        self.assertAlmostEqual(areas["experiment_focused_blur42"], model.shadow_quad(model.CARD_W, model.CARD_H, 42))
        self.assertAlmostEqual(areas["reference_halo_blur90"], model.shadow_quad(model.CARD_W - 16, model.CARD_H - 16, 90))

    def test_grid_fractions_follow_from_areas(self):
        grids = FACTS["perf_math"]["grid_shadow_area_px"]
        fractions = FACTS["perf_math"]["grid_fraction_of_1080p"]
        for key, area in grids.items():
            self.assertAlmostEqual(fractions[key], area / model.FRAME_1080P_PX, places=12)
        self.assertAlmostEqual(FACTS["perf_math"]["ratios"]["experiment_over_current_focused"], 1.1248778755, places=9)

    def test_arithmetic_labels_stay_honest(self):
        self.assertIn("MODEL", FACTS["labels"]["perf_math"])
        self.assertEqual(FACTS["labels"]["native_runs"], "NOT_RUN")
        for gate in ("native_build", "rendering", "frame_pacing", "physical_tv", "visual_difference"):
            self.assertNotEqual(FACTS["gates"][gate], "MEASURED", gate)
        self.assertIn("BLOCKED", FACTS["gates"]["native_build"])
        self.assertIn("NOT_RUN", FACTS["gates"]["visual_difference"])


class DocumentationAndHygieneTests(unittest.TestCase):
    def test_documented_cache_budgets_match_code(self):
        self.assertTrue(FACTS["budgets"]["match"])
        docs, code = FACTS["budgets"]["docs"], FACTS["budgets"]["code"]
        self.assertEqual(docs["glyph_geometry_mib"] * 1024 * 1024, code["glyph_geometry_bytes"])
        self.assertEqual(docs["text_runs_mib"] * 1024 * 1024, code["text_bytes"])
        self.assertEqual(docs["raster_mib"] * 1024 * 1024, code["raster_bytes"])

    def test_no_embedded_credentials_or_drm_code(self):
        hygiene = FACTS["hygiene"]
        self.assertEqual(sum(hygiene["secret_patterns"].values()), 0)
        self.assertEqual(sum(hygiene["drm_patterns"].values()), 0)

    def test_lg_headers_are_included_not_vendored(self):
        headers = FACTS["hygiene"]["lg_header_includes"]
        self.assertFalse(headers["vendored_header_present"])
        self.assertGreaterEqual(headers["NDL_directmedia.h"], 1)
        self.assertTrue(headers["smp_api_is_own_facade"])

    def test_assets_are_licensed_and_large(self):
        assets = FACTS["assets"]
        if not assets["available"]:
            self.skipTest("reference tree.json not cached")
        self.assertEqual(assets["ofl_license_files"], 36)
        self.assertGreater(assets["font_bytes"], 0)
        self.assertGreater(assets["total_bytes"], 100_000_000)


class DiagnosticsTests(unittest.TestCase):
    def test_our_diagnostics_superset_the_reference(self):
        diagnostics = FACTS["diagnostics"]
        self.assertTrue(diagnostics["ours_superset"])
        self.assertTrue(diagnostics["ours_has_timeline"])
        self.assertFalse(diagnostics["reference_has_timeline"])
        self.assertIn("timeline", diagnostics["ours_fields"])


class ReportTests(unittest.TestCase):
    def test_report_states_pin_and_unrun_evidence(self):
        report = (ROOT / "research/luma-audit/REFERENCE-LAUNCHER-COMPARISON.md").read_text()
        self.assertIn(PIN, report)
        self.assertIn("NOT_RUN", report)
        self.assertIn("BLOCKED", report)
        self.assertIn("MODEL", report)


if __name__ == "__main__":
    unittest.main()
