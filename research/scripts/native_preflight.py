#!/usr/bin/env python3
"""Read-only native desktop validation preflight. No installs or native builds.

Writes delivery/native-validation-status.json and exits 1 while required tools
or generated inputs are missing. Exit 0 means ready to run the manual runbook,
not that any native test has passed.
"""
from __future__ import annotations
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "delivery/native-validation-status.json"
REQUIRED = {
    "node_runtime": ["node", "pnpm"],
    "rust": ["cargo", "rustc", "rustfmt", "clippy-driver"],
    "native_deps": ["pkg-config", "sdl2-config", "cmake", "woff2_decompress"],
    "python_assets": ["python3"],
    "desktop_smoke": ["xvfb-run", "Xvfb", "xauth"],
    "repo": ["git"],
}
OPTIONAL = {"reference_shell": ["nix"], "rust_manager": ["rustup"]}


def version(tool: str, args: list[str]) -> dict:
    path = shutil.which(tool)
    if not path:
        return {"available": False, "version": None}
    if not args:
        return {"available": True, "version": None, "note": "presence only"}
    try:
        result = subprocess.run([tool, *args], cwd=ROOT, capture_output=True, text=True, timeout=10, check=False)
        output = (result.stdout or result.stderr).strip()
        return {"available": True, "version": output.splitlines()[0] if output else None, "exit_code": result.returncode}
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"available": True, "version": None, "error": type(error).__name__}


def main() -> int:
    probes = {tool: version(tool, args) for group in REQUIRED.values() for tool, args in
              [(t, ["--version"] if t not in {"xvfb-run", "Xvfb", "xauth", "woff2_decompress"} else []) for t in group]}
    for group in OPTIONAL.values():
        for tool in group:
            probes[tool] = version(tool, ["--version"])
    missing = sorted(tool for tool, probe in probes.items() if not probe["available"] and tool in {t for g in REQUIRED.values() for t in g})
    optional_missing = sorted(tool for tool, probe in probes.items() if not probe["available"] and tool in {t for g in OPTIONAL.values() for t in g})
    fonttools = subprocess.run(["python3", "-c", "import fontTools; print(fontTools.version)"], cwd=ROOT, capture_output=True, text=True, check=False) if shutil.which("python3") else None
    fonttools_ok = bool(fonttools and fonttools.returncode == 0)
    if not fonttools_ok:
        missing.append("python3-fontTools")
    sdl2 = None
    if shutil.which("pkg-config"):
        result = subprocess.run(["pkg-config", "--modversion", "sdl2"], cwd=ROOT, capture_output=True, text=True, check=False)
        sdl2 = {"available": result.returncode == 0, "version": result.stdout.strip() if result.returncode == 0 else None}
    else:
        sdl2 = {"available": False, "version": None, "reason": "pkg-config missing"}
    if not sdl2["available"]:
        missing.append("SDL2-development (pkg-config sdl2)")
    node_modules = (ROOT / "node_modules").is_dir()
    if not node_modules:
        missing.append("node_modules (pnpm install --frozen-lockfile)")
    assets = (ROOT / ".build/assets/version.txt").is_file()
    binary = (ROOT / "target/debug/luma").is_file()
    inputs = {"node_modules": node_modules, "generated_assets": assets, "desktop_binary": binary,
              "sdl2_pkg_config": sdl2, "python_fonttools": {"available": fonttools_ok, "version": fonttools.stdout.strip() if fonttools_ok else None}}
    ready = not missing and assets and binary
    status = {"schema": "luma-native-validation-status/1",
              "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip(),
              "head_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "ready": ready, "status": "READY" if ready else "BLOCKED",
              "missing_required": sorted(set(missing)), "missing_optional": optional_missing,
              "tools": probes, "inputs": inputs,
              "automatic_install": False, "native_tests_run": False, "physical_tv_commands": 0,
              "runbook": "delivery/NATIVE-VALIDATION.md",
              "setup_commands_manual_only": ["nix develop", "pnpm install --frozen-lockfile", "pnpm assets", "cargo build --locked --package luma --no-default-features"]}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(status, indent=2) + "\n")
    print(json.dumps({"status": status["status"], "missing_required": status["missing_required"], "missing_optional": optional_missing, "output": str(OUT.relative_to(ROOT))}))
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
