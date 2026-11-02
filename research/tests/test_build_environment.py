import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class BuildEnvironment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = json.loads((ROOT / "delivery/build-environment.json").read_text())

    def test_spec_is_manual_and_device_free(self):
        self.assertFalse(self.spec["automatic_install"])
        self.assertEqual(self.spec["network_requests"], 0)
        self.assertEqual(self.spec["native_builds"], 0)
        self.assertEqual(self.spec["device_commands"], 0)
        self.assertFalse(any("deploy" in c["command"] for c in self.spec["expected_commands"]))

    def test_reference_pins_come_from_repository_configuration(self):
        self.assertEqual(self.spec["reference"]["rust"]["ci_and_flake"], "1.93.0")
        self.assertEqual(self.spec["reference"]["rust"]["msrv"], "1.88")
        self.assertEqual(self.spec["reference"]["pnpm"], "pnpm@10.34.5")
        self.assertEqual(self.spec["cargo"]["locked_package_count"], 116)
        self.assertEqual(self.spec["node"]["dev_dependencies"]["oxlint"], "1.88.0")
        self.assertTrue(all(f["matches"] for f in self.spec["fonts"]))

    def test_cross_build_preserves_abi_and_isolated_pkg_config(self):
        webos = self.spec["webos"]
        self.assertEqual(webos["target"], "armv7-unknown-linux-gnueabi")
        self.assertIn("-soft-float", webos["rustflags"])
        self.assertIn("PKG_CONFIG_PATH empty", webos["pkg_config"])
        self.assertEqual(webos["sdk_archive_checksum_status"], "NOT_PINNED_IN_REPOSITORY")
        self.assertEqual(len(webos["sdl_archive_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
