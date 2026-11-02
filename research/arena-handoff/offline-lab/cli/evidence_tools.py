#!/usr/bin/env python3
"""Versioned, sanitized evidence export and offline receipt correlation.

Only stdlib dependencies. Legacy scan documents are accepted as input; the
normalized package never upgrades missing or unsupported values to zero.
"""
import json
import math
import os
import re
import subprocess

SCHEMA_VERSION = "1.0.0"
SENSITIVE_KEY = re.compile(r"(serial|device.?id|(^id$|_id$|identifier)|mac|host.?name|ssid|credential|password|token|secret|user(name)?|email)", re.I)
IPV4 = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])")
IPV6 = re.compile(r"(?i)(?<![0-9a-f:])(?:[0-9a-f]{0,4}:){2,7}[0-9a-f]{0,4}(?![0-9a-f:])")
MAC = re.compile(r"(?i)(?<![0-9a-f])(?:[0-9a-f]{2}:){5}[0-9a-f]{2}(?![0-9a-f])")


def _commit_sha():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    try:
        return subprocess.check_output(["git", "-C", root, "rev-parse", "HEAD"],
                                       stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        return "UNKNOWN"


def _redact(value, key=""):
    if SENSITIVE_KEY.search(key):
        return "REDACTED" if value not in (None, "", [], {}) else value
    if isinstance(value, dict):
        return {k: _redact(v, k) for k, v in value.items()
                if k.lower() not in ("lens_root", "root_path")}
    if isinstance(value, list):
        return [_redact(v) for v in value]
    if isinstance(value, str):
        value = MAC.sub("[REDACTED_MAC]", value)
        value = IPV4.sub("[REDACTED_IP]", value)
        return IPV6.sub("[REDACTED_IP]", value)
    return value


def _metric(metric_id, value, unit, source, evidence_class, status="AVAILABLE"):
    return {"id": metric_id, "value": value, "unit": unit, "source": source,
            "evidence_class": evidence_class, "status": status}


def _safe_legacy_report(scan):
    """Keep compatibility context but suppress legacy placeholder zeros."""
    report = _redact(scan)
    caps = scan.get("capabilities") or {}
    if not caps.get("proc_mounts"):
        report.setdefault("mounts", {}).update(count=None, evidence="NOT_RUN")
    if not (caps.get("proc_net_tcp") or caps.get("proc_net_tcp6")):
        report.setdefault("network", {}).update(listen_count=None, listen_ports=None, evidence="NOT_RUN")
    if not caps.get("process_listing") or (scan.get("processes") or {}).get("evidence") == "HOST":
        report.setdefault("processes", {}).update(count=None)
    for section in ("apps", "ls2_policy"):
        if (scan.get(section) or {}).get("evidence") == "NOT_RUN":
            report.setdefault(section, {}).update(count=None, entries=None)
    if (scan.get("luna") or {}).get("status") != "OBSERVED":
        report.setdefault("luna", {}).update(listapps_count=None)
    return report


def export_evidence(scan, source_environment=None):
    """Normalize an existing legacy report without upgrading unknown data."""
    scan = scan if isinstance(scan, dict) else json.load(open(scan, encoding="utf-8"))
    meta = scan.get("meta") or {}
    osinfo = scan.get("os") or {}
    scope = meta.get("scope", "unknown")
    mode = meta.get("mode", "unknown")
    env = source_environment or ("mock" if scope == "mock" or mode == "host" else "unknown")
    if env not in ("mock", "desktop", "emulator", "physical_tv", "unknown"):
        raise ValueError("source environment must be mock, desktop, emulator, physical_tv, or unknown")

    timestamp = meta.get("ts")
    clock_source = "collector_system_utc" if timestamp and timestamp != "unknown" else "UNKNOWN"
    warnings = []
    if scope in ("mock", "host") or env in ("mock", "desktop"):
        warnings.append("Non-device or host-derived observations are not physical-TV evidence.")
    firmware_identity = osinfo.get("version_id") or osinfo.get("pretty") or None
    firmware_confidence = "inferred_from_os_release" if firmware_identity else "UNKNOWN"
    if firmware_identity:
        warnings.append("Firmware identity is reported by os-release and is not cryptographically verified.")

    metrics = []
    def add_count(metric_id, section, field, unit, source, evidence_key="evidence"):
        obj = scan.get(section) or {}
        ev = obj.get(evidence_key, "NOT_RUN")
        value = obj.get(field)
        valid = ev in ("OBSERVED", "MEASURED") and isinstance(value, (int, float)) and not isinstance(value, bool)
        metrics.append(_metric(metric_id, value if valid else None, unit, source,
                               ev if valid else "NOT_RUN", "AVAILABLE" if valid else "UNKNOWN"))
    add_count("network.listen_socket_count", "network", "listen_count", "count", "/proc/net/tcp and tcp6")
    add_count("applications.installed_count", "apps", "count", "count", "application metadata census")
    add_count("ls2.policy_file_count", "ls2_policy", "count", "count", "LS2 policy directory census")
    caps_in = scan.get("capabilities") or {}
    for m in metrics:
        if m["id"] == "network.listen_socket_count" and not (caps_in.get("proc_net_tcp") or caps_in.get("proc_net_tcp6")):
            m.update(value=None, evidence_class="NOT_RUN", status="UNKNOWN")
    proc = scan.get("processes") or {}
    proc_ev = proc.get("evidence", "NOT_RUN")
    proc_value = proc.get("count")
    proc_valid = proc_ev == "OBSERVED" and isinstance(proc_value, (int, float)) and not isinstance(proc_value, bool) and env == "physical_tv"
    metrics.append(_metric("processes.process_count", proc_value if proc_valid else None,
                           "count", "ps process listing", proc_ev if proc_valid else "NOT_RUN",
                           "AVAILABLE" if proc_valid else "UNKNOWN"))
    # No process memory or compositing-layer estimate is currently collected.
    metrics.append(_metric("processes.memory", None, "bytes", "NOT_COLLECTED", "NOT_RUN", "UNKNOWN"))
    metrics.append(_metric("compositing.layer_memory_estimate", None, "bytes", "NOT_COLLECTED", "NOT_RUN", "UNKNOWN"))

    caps = {
        "proc_mounts": bool((scan.get("capabilities") or {}).get("proc_mounts", False)),
        "proc_net_tcp": bool((scan.get("capabilities") or {}).get("proc_net_tcp", False)),
        "proc_net_tcp6": bool((scan.get("capabilities") or {}).get("proc_net_tcp6", False)),
        "process_listing": bool((scan.get("capabilities") or {}).get("process_listing", False)),
        "luna_send": bool((scan.get("capabilities") or {}).get("luna_send", False)),
        "root_scope": scope == "root",
        "read_only_collection": True,
    }
    sensors = {
        "mount_table": "AVAILABLE" if caps["proc_mounts"] else "UNKNOWN",
        "network_sockets": "AVAILABLE" if caps["proc_net_tcp"] or caps["proc_net_tcp6"] else "UNKNOWN",
        "process_table": "AVAILABLE" if caps["process_listing"] else "UNKNOWN",
        "installed_apps": (scan.get("apps") or {}).get("evidence", "NOT_RUN"),
        "luna_list_apps": (scan.get("luna") or {}).get("status", "NOT_RUN"),
    }
    provenance = [
        {"operation": "read operating-system identity and UTC clock", "command": "uname; date -u; id -u", "read_only": True},
        {"operation": "read mount and socket tables; inspect available storage", "command": "read /proc/mounts and /proc/net/tcp[6]; df -k", "read_only": True},
        {"operation": "enumerate process names/count when available", "command": "ps; awk; sort", "read_only": True},
        {"operation": "read app metadata and DNS resolver configuration", "command": "read appinfo.json and /etc/resolv.conf", "read_only": True},
        {"operation": "hash LS2 policy files without emitting file contents", "command": "sha256sum selected policy files", "read_only": True},
        {"operation": "optional public application-manager query", "command": "luna-send listApps (only when available)", "read_only": True},
    ]
    agent = scan.get("lens") or {}
    return {
        "schema_version": SCHEMA_VERSION,
        "collected_at": {"timestamp": timestamp or None, "clock_source": clock_source},
        "specimen": {"device_identity": "UNKNOWN", "identity_confidence": "UNKNOWN"},
        "firmware": {"identity": firmware_identity, "verification_confidence": firmware_confidence},
        "agent": {"name": "webos-lens", "version": agent.get("version", "UNKNOWN"),
                   "commit_sha": _commit_sha()},
        "source_environment": env,
        "collection_capabilities": caps,
        "sensor_availability": sensors,
        "measurements": metrics,
        "read_only_command_provenance": provenance,
        "data_quality_warnings": warnings,
        "sanitization": {"applied": True, "policy": "sensitive-key, IPv4/IPv6 and MAC redaction; local root paths omitted"},
        "source_report": _safe_legacy_report(scan),
    }


def _measurement_list(doc):
    if isinstance(doc.get("measurements"), list):
        return doc["measurements"]
    # Nuvio/GHUI receipts can represent metrics as either list or mapping.
    result = []
    vals = doc.get("metrics", {})
    if isinstance(vals, dict):
        for name, obj in vals.items():
            if isinstance(obj, dict):
                result.append(dict(obj, id=obj.get("id", name)))
            else:
                result.append({"id": name, "value": obj, "unit": "UNKNOWN",
                               "evidence_class": "UNKNOWN", "source": "receipt"})
    elif isinstance(vals, list):
        result = vals
    return result


def correlate(device, browser, alignment):
    """Only label comparisons legitimate when alignment is explicitly verified."""
    if not isinstance(device, dict): device = json.load(open(device, encoding="utf-8"))
    if not isinstance(browser, dict): browser = json.load(open(browser, encoding="utf-8"))
    if not isinstance(alignment, dict): alignment = json.load(open(alignment, encoding="utf-8"))
    status = alignment.get("status")
    method = alignment.get("method")
    clocks = alignment.get("clock_domains")
    error = alignment.get("max_error_ms")
    aligned = (status == "verified" and bool(method) and isinstance(clocks, dict) and
               bool(clocks.get("device")) and bool(clocks.get("browser")) and
               isinstance(error, (int, float)) and math.isfinite(error) and error >= 0 and
               bool(alignment.get("evidence")) and alignment.get("same_specimen") is True)
    device_fw = (device.get("firmware") or {}).get("identity")
    browser_fw = browser.get("firmware_identity")
    firmware_match = (device_fw == browser_fw) if device_fw and browser_fw else None
    ds = {m.get("id"): m for m in device.get("measurements", []) if isinstance(m, dict)}
    bs = {m.get("id"): m for m in _measurement_list(browser) if isinstance(m, dict)}
    comparisons = []
    for mid in sorted(set(ds) & set(bs)):
        if "composit" in mid.lower() or "estimate" in mid.lower():
            continue
        left, right = ds[mid], bs[mid]
        units_match = left.get("unit") == right.get("unit") and left.get("unit") not in (None, "UNKNOWN")
        measured = left.get("evidence_class") in ("MEASURED", "OBSERVED") and right.get("evidence_class") in ("MEASURED", "OBSERVED")
        numeric = all(isinstance(x.get("value"), (int, float)) and not isinstance(x.get("value"), bool) for x in (left, right))
        ok = aligned and firmware_match is not False and units_match and measured and numeric
        reason = "comparable" if ok else ("time alignment or same-specimen binding is not explicitly verified" if not aligned else
                  "device firmware identity conflicts with browser receipt" if firmware_match is False else
                  "units differ or are unknown" if not units_match else
                  "one or both values are not measured/observed" if not measured else "value is unavailable")
        comparisons.append({"measurement_id": mid, "comparable": ok, "reason": reason,
                            "device": {"value": left.get("value"), "unit": left.get("unit"), "evidence_class": left.get("evidence_class")},
                            "browser": {"value": right.get("value"), "unit": right.get("unit"), "evidence_class": right.get("evidence_class")}})
    # Memory classes are intentionally listed separately, never paired by name resemblance.
    device_memory = [m.get("id") for m in device.get("measurements", [])
                     if isinstance(m, dict) and ("memory" in str(m.get("id", "")).lower() or "composit" in str(m.get("id", "")).lower())]
    browser_memory = [m.get("id") for m in _measurement_list(browser)
                      if isinstance(m, dict) and ("memory" in str(m.get("id", "")).lower() or "composit" in str(m.get("id", "")).lower())]
    return {
        "schema_version": "1.0.0",
        "report_type": "webos-lens-browser-correlation",
        "alignment": {"verified": aligned, "record_id": _redact(alignment.get("record_id"), "record_id"),
                      "clock_domains": _redact(clocks) if aligned else None,
                      "method": _redact(method, "method") if aligned else None, "max_error_ms": error if aligned else None,
                      "reason": "explicit verified alignment record accepted" if aligned else
                      "timestamp proximity alone is insufficient; provide verified clock-domain alignment"},
        "device_firmware": device.get("firmware", {}),
        "browser_firmware_identity": browser_fw,
        "firmware_identity_match": firmware_match,
        "comparisons": comparisons,
        "unmatched_metrics": {
            "device_only": sorted(set(ds) - set(bs)),
            "browser_only": sorted(set(bs) - set(ds)),
            "reason": "metric IDs must match exactly; no semantic equivalence is inferred"
        },
        "separate_memory_measurements": {"device_metric_ids": device_memory,
                                          "browser_metric_ids": browser_memory,
                                          "rule": "measured process memory and theoretical compositing-layer estimates are never merged"},
    }
