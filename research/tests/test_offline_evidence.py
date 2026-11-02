"""Synthetic-only checks of the unchanged bundled evidence processor.

No TV, scan collection, network, external fixture or full JSON-Schema validator.
The bundled exporter's agent SHA is current checkout HEAD, not origin proof.
"""
import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "research/arena-handoff/offline-lab/cli/evidence_tools.py"
spec = importlib.util.spec_from_file_location("bundled_evidence", MODULE)
evidence = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evidence)


def scan():
    return {"meta": {"scope": "mock", "mode": "host", "ts": "2026-11-02T00:00:00Z"},
            "os": {"version_id": "synthetic-os"}, "capabilities": {},
            "network": {"listen_count": 0, "evidence": "NOT_RUN"},
            "processes": {"count": 99, "evidence": "HOST"},
            "apps": {"count": 0, "evidence": "NOT_RUN"},
            "serial": "SYNTHETIC-PRIVATE", "host_name": "private.example",
            "note": "192.0.2.10 02:00:00:00:00:01"}


def metric(value=5, unit="ms", kind="MEASURED", mid="native.test"):
    return {"id": mid, "value": value, "unit": unit, "source": "synthetic", "evidence_class": kind}


def alignment():
    return {"status": "verified", "method": "synthetic shared marker", "max_error_ms": 1,
            "clock_domains": {"device": "synthetic-monotonic", "browser": "synthetic-native"},
            "same_specimen": True, "evidence": "synthetic-only"}


class ExportTests(unittest.TestCase):
    def test_missing_and_host_values_stay_unknown(self):
        doc = evidence.export_evidence(scan(), "mock")
        values = {m["id"]: m for m in doc["measurements"]}
        for key in ("network.listen_socket_count", "processes.process_count", "processes.memory", "compositing.layer_memory_estimate"):
            self.assertIsNone(values[key]["value"])
            self.assertEqual(values[key]["status"], "UNKNOWN")
        self.assertEqual(doc["source_environment"], "mock")
        self.assertEqual(doc["specimen"]["device_identity"], "UNKNOWN")

    def test_sensitive_values_are_redacted(self):
        raw = json.dumps(evidence.export_evidence(scan(), "mock"))
        for private in ("SYNTHETIC-PRIVATE", "private.example", "192.0.2.10", "02:00:00:00:00:01"):
            self.assertNotIn(private, raw)

    def test_invalid_environment_refused(self):
        with self.assertRaises(ValueError):
            evidence.export_evidence(scan(), "invented")

    def test_agent_sha_provenance_caveat(self):
        doc = evidence.export_evidence(scan(), "mock")
        self.assertRegex(doc["agent"]["commit_sha"], r"^[0-9a-f]{40}$")
        self.assertNotEqual(doc["agent"]["commit_sha"], "e5811544ec464666401e5306a420f5363076f88e")


class CorrelationTests(unittest.TestCase):
    def setUp(self):
        self.device = {"firmware": {"identity": "synthetic"}, "measurements": [metric()]}
        self.native = {"firmware_identity": "synthetic", "metrics": [metric(6)]}

    def compare(self, a=None):
        return evidence.correlate(self.device, self.native, a or alignment())["comparisons"][0]["comparable"]

    def test_verified_matching_units_compare(self):
        self.assertTrue(self.compare())

    def test_timestamp_proximity_or_missing_binding_does_not_compare(self):
        for key, value in (("status", "unverified"), ("same_specimen", False), ("evidence", ""), ("max_error_ms", float("nan")), ("max_error_ms", -1)):
            a = alignment(); a[key] = value
            with self.subTest(key=key): self.assertFalse(self.compare(a))

    def test_firmware_and_unit_conflicts_refused(self):
        self.native["firmware_identity"] = "different"
        self.assertFalse(self.compare())
        self.native["firmware_identity"] = "synthetic"
        self.native["metrics"][0]["unit"] = "count"
        self.assertFalse(self.compare())

    def test_unknown_value_and_estimated_memory_do_not_compare(self):
        self.native["metrics"][0]["evidence_class"] = "NOT_RUN"
        self.assertFalse(self.compare())
        self.native["metrics"][0] = metric(6, mid="compositing.layer_memory_estimate")
        self.device["measurements"][0] = metric(mid="compositing.layer_memory_estimate")
        self.assertEqual(evidence.correlate(self.device, self.native, alignment())["comparisons"], [])

    def test_unmatched_names_remain_separate(self):
        self.native["metrics"][0]["id"] = "native.other"
        result = evidence.correlate(self.device, self.native, alignment())
        self.assertEqual(result["comparisons"], [])
        self.assertEqual(result["unmatched_metrics"]["device_only"], ["native.test"])
        self.assertEqual(result["unmatched_metrics"]["browser_only"], ["native.other"])


class StaticContractTests(unittest.TestCase):
    def test_protected_functions_have_no_disposable_service_inference(self):
        doc = json.loads((ROOT / "research/arena-handoff/references/lg-feature-dependencies.json").read_text())
        protected = set(doc["protected_functions"]["list"])
        edges = {edge["feature"]: edge for edge in doc["edges"]}
        self.assertTrue(protected <= set(edges))
        for feature in protected:
            self.assertTrue(edges[feature]["protected"])
        self.assertIn("UNKNOWN", doc["classification_policy"])

    def test_preflight_unknown_is_not_ready(self):
        fixture = json.loads((ROOT / "research/fixtures/device-preflight-not-ready.json").read_text())
        self.assertEqual(fixture["verdict"], "NOT-READY")
        self.assertFalse(fixture["recovery_readiness"]["verified"])
        self.assertEqual(fixture["forbidden_ops"]["executed"], [])
        self.assertTrue(any(v == "UNKNOWN" for v in fixture["protected_functions"].values()))

if __name__ == "__main__":
    unittest.main()
