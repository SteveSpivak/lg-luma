import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from reference_launcher import (
    CARD_H,
    CARD_W,
    FRAME_1080P_PX,
    FRAME_4K_PX,
    bandwidth_gbs,
    chase_rate,
    chase_settle,
    chase_tau,
    composite_alpha,
    contrast,
    damage_area,
    depth_index,
    equivalent_damping,
    fill_bytes,
    grid_shadow_area,
    penumbra_ring,
    pop,
    pop_peak,
    pop_peak_k,
    pop_settle_k,
    rgba_bytes,
    shadow_quad,
    softness,
    zoom_area_factor,
)


class ShadowGeometryTests(unittest.TestCase):
    def test_shadow_quad_uses_inset_by_blur_rule(self):
        # src/renderer.rs draws shadows as rect.inset(-blur); src/damage.rs uses blur + 1.
        self.assertAlmostEqual(shadow_quad(256, 154.4, 22), 59520.0)
        self.assertAlmostEqual(shadow_quad(256, 154.4, 34), 72057.6)
        self.assertAlmostEqual(shadow_quad(256, 154.4, 42), 81056.0)
        self.assertAlmostEqual(shadow_quad(256, 154.4, 26), 63571.2)
        self.assertAlmostEqual(shadow_quad(256, 154.4, 40), 78758.4)
        self.assertAlmostEqual(shadow_quad(240, 138.4, 90), 133728.0)

    def test_experiment_growth_is_the_focused_delta_only(self):
        current = shadow_quad(CARD_W, CARD_H, 34)
        experiment = shadow_quad(CARD_W, CARD_H, 42)
        self.assertAlmostEqual(experiment / current, 1.1248778755, places=9)
        self.assertAlmostEqual(experiment - current, 8998.4, places=6)
        # Upstream's layered focus (40 blur + 90 blur halo) is 2.6x the experiment's area.
        reference = shadow_quad(CARD_W, CARD_H, 40) + shadow_quad(CARD_W - 16, CARD_H - 16, 90)
        self.assertAlmostEqual(experiment / reference, 0.3814644137, places=9)

    def test_penumbra_ring_is_soft_band_only(self):
        self.assertAlmostEqual(penumbra_ring(CARD_W, CARD_H, 42), 81056.0 - CARD_W * CARD_H)

    def test_damage_rule_expands_by_blur_plus_one(self):
        self.assertAlmostEqual(damage_area(CARD_W, CARD_H, 22), 60520.8)
        self.assertAlmostEqual(damage_area(CARD_W, CARD_H, 34), 73154.4)
        self.assertAlmostEqual(damage_area(CARD_W, CARD_H, 42), 82216.8)
        self.assertAlmostEqual(damage_area(CARD_W, CARD_H, 42) - damage_area(CARD_W, CARD_H, 34), 9062.4, places=6)

    def test_grid_area_honours_zero_resting_blur(self):
        self.assertAlmostEqual(grid_shadow_area(14, 1, 22, 42), 14 * 59520.0 + 81056.0)
        self.assertAlmostEqual(grid_shadow_area(14, 1, 0, 42), 81056.0)
        self.assertAlmostEqual(grid_shadow_area(0, 1, 0, 42, 133728.0), 81056.0 + 133728.0)


class MotionTests(unittest.TestCase):
    def test_chase_matches_documented_settle(self):
        self.assertAlmostEqual(chase_rate(), 17.8888888889, places=9)
        self.assertAlmostEqual(chase_tau(), 0.0559006211, places=9)
        self.assertAlmostEqual(chase_settle(0.96), 0.179937, places=6)
        self.assertAlmostEqual(chase_settle(0.99), 0.257432, places=6)
        self.assertAlmostEqual(chase_settle(0.96) * 60, 10.7962, places=4)

    def test_spring_peak_is_analytic_turning_point(self):
        k = pop_peak_k()
        self.assertAlmostEqual(k, 0.2677945045, places=9)
        self.assertAlmostEqual(pop_peak(), 1.2344426467, places=9)
        self.assertAlmostEqual(pop(k), pop_peak(), places=12)
        # Derivate vanishes there: decay*cos + freq*sin == 0.
        self.assertAlmostEqual(5 * __import__("math").cos(10 * k) + 10 * __import__("math").sin(10 * k), 0.0, places=9)

    def test_spring_is_not_a_true_second_order_response(self):
        # 1 - e^-5k cos(10k) has no sine term, so its damping is only *equivalent*.
        overshoot = pop_peak() - 1
        self.assertAlmostEqual(overshoot, 0.2344426467, places=9)
        self.assertAlmostEqual(equivalent_damping(overshoot), 0.4191959858, places=9)
        self.assertLess(abs(pop(0.0)), 1e-12)
        self.assertAlmostEqual(pop_settle_k() * 0.55, 0.5065687205, places=9)

    def test_zoom_area_growth_at_peak(self):
        self.assertAlmostEqual(1 + 0.07 * pop_peak(), 1.0864109853, places=9)
        self.assertAlmostEqual(zoom_area_factor(1 + 0.07 * pop_peak()), 1.1802888289, places=9)

    def test_invalid_inputs_raise(self):
        for call in (
            lambda: chase_rate(0),
            lambda: chase_settle(0),
            lambda: chase_settle(1),
            lambda: equivalent_damping(0),
            lambda: shadow_quad(10, 10, -1),
            lambda: composite_alpha(1.2),
            lambda: contrast(10, 0),
            lambda: grid_shadow_area(-1, 0, 0, 0),
        ):
            with self.assertRaises(ValueError):
                call()


class DesignMetricTests(unittest.TestCase):
    def test_dimensionless_depth_and_softness(self):
        self.assertAlmostEqual(depth_index(20), 0.1295336788, places=9)
        self.assertAlmostEqual(depth_index(14), 0.0906735751, places=9)
        self.assertAlmostEqual(depth_index(12), 0.0777202073, places=9)
        self.assertAlmostEqual(softness(42), 0.2720207254, places=9)
        self.assertAlmostEqual(softness(40), 0.2590673575, places=9)
        self.assertAlmostEqual(contrast(42, 20), 2.1)
        self.assertAlmostEqual(contrast(40, 12), 3.3333333333, places=9)

    def test_stacked_alpha_is_not_additive(self):
        self.assertAlmostEqual(composite_alpha(0.24, 0.3), 0.468)
        self.assertAlmostEqual(composite_alpha(0.5), 0.5)
        self.assertAlmostEqual(composite_alpha(), 0.0)


class FrameBudgetTests(unittest.TestCase):
    def test_rgba_payload_arithmetic(self):
        self.assertEqual(rgba_bytes(1920, 1080), 8294400)
        self.assertEqual(rgba_bytes(3840, 2160), 33177600)
        self.assertEqual(2 * rgba_bytes(3840, 2160), 66355200)
        self.assertEqual(FRAME_1080P_PX, 2073600)
        self.assertEqual(FRAME_4K_PX, 8294400)

    def test_bandwidth_is_arithmetic_not_gpu_measurement(self):
        self.assertAlmostEqual(bandwidth_gbs(rgba_bytes(1920, 1080), 60), 0.497664)
        self.assertAlmostEqual(fill_bytes(914336.0, traffic=2), 7314688.0)
        self.assertAlmostEqual(bandwidth_gbs(fill_bytes(914336.0, traffic=2), 60), 0.43888128)


if __name__ == "__main__":
    unittest.main()
