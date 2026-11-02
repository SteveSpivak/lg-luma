#!/usr/bin/env python3
"""Derive a manual build-environment specification from pinned repository files.

Read-only with respect to dependencies: no install, network, Nix evaluation,
native build, SDK download or device command. Writes delivery/build-environment.json.
"""
from __future__ import annotations
import hashlib
import json
import re
import shutil
import subprocess
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "e5608cd053be5376a54a806129a332952dfabcef"
OUT = ROOT / "delivery/build-environment.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text(path: str) -> str:
    return (ROOT / path).read_text()


def probe(tool: str, args: list[str]) -> dict:
    path = shutil.which(tool)
    if not path:
        return {"available": False, "version": None}
    if not args:
        return {"available": True, "version": None, "note": "Presence only; no execution"}
    try:
        result = subprocess.run([tool, *args], cwd=ROOT, capture_output=True, text=True, timeout=5, check=False)
        return {"available": True, "version": (result.stdout or result.stderr).strip().splitlines()[0] if (result.stdout or result.stderr).strip() else None,
                "exit_code": result.returncode}
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"available": True, "version": None, "error": type(error).__name__}


def main() -> int:
    cargo = tomllib.loads(text("Cargo.toml"))
    lock = tomllib.loads(text("Cargo.lock"))
    package = json.loads(text("package.json"))
    flake_lock = json.loads(text("flake.lock"))
    locked = {p["name"]: p["version"] for p in lock["package"]}
    direct = []
    for manifest in ("Cargo.toml", "vector-geometry/Cargo.toml", "tools/vector-assets/Cargo.toml", "tv-helper/Cargo.toml"):
        data = tomllib.loads(text(manifest))
        for name, spec in data.get("dependencies", {}).items():
            direct.append({"manifest": manifest, "name": name, "spec": spec, "locked_version": locked.get(name)})
    ci = text(".github/workflows/ci.yml")
    flake = text("flake.nix")
    runtime = text("tools/webos-runtime.mjs")
    sdk = text("tools/setup-webos-sdk.mjs")
    font_source = text("tools/font-assets.mjs")
    fonts = []
    for name, expected in re.findall(r"\[\s*'([^']+\.(?:ttf|txt))',\s*'[^']+',\s*'([0-9a-f]{64})'", font_source):
        path = ROOT / "assets/fonts" / name
        actual = sha(path) if path.is_file() else None
        fonts.append({"name": name, "expected_sha256": expected, "actual_sha256": actual, "matches": actual == expected})
    sdk_urls = re.findall(r"'(https://github.com/[^']+_sdk-buildroot[^']*)'", sdk)
    sdl_archive = re.search(r"archiveHash = '([0-9a-f]{64})'", runtime).group(1)
    sdl_library = re.search(r"libraryHash = '([0-9a-f]{64})'", runtime).group(1)
    nodes = flake_lock["nodes"]
    commands = [
        {"phase": "enter-reference-shell", "command": "nix develop", "manual": True, "may_fetch_or_build": True, "status": "NOT_RUN"},
        {"phase": "node-dependencies", "command": "pnpm install --frozen-lockfile", "manual": True, "may_fetch_or_build": True, "status": "NOT_RUN"},
        {"phase": "format", "command": "pnpm format:check", "manual": True, "status": "BLOCKED_NATIVE_TOOLCHAIN"},
        {"phase": "lint-version", "command": "pnpm check", "manual": True, "status": "BLOCKED_NATIVE_TOOLCHAIN"},
        {"phase": "unit-tests", "command": "pnpm test", "manual": True, "status": "BLOCKED_NATIVE_TOOLCHAIN"},
        {"phase": "assets", "command": "pnpm assets", "manual": True, "status": "BLOCKED_NATIVE_TOOLCHAIN"},
        {"phase": "desktop-build", "command": "cargo build --locked --package luma --no-default-features", "manual": True, "status": "BLOCKED_NATIVE_TOOLCHAIN"},
        {"phase": "desktop-smoke", "command": "LIBGL_ALWAYS_SOFTWARE=1 LUMA_SMOKE_SKIP_BUILD=1 xvfb-run -a -s '-screen 0 1920x1080x24' node tests/smoke.mjs", "manual": True, "status": "BLOCKED_NATIVE_TOOLCHAIN"},
        {"phase": "desktop-smoke", "command": "LIBGL_ALWAYS_SOFTWARE=1 LUMA_SMOKE_SKIP_BUILD=1 xvfb-run -a -s '-screen 0 1920x1080x24' node tests/brands-smoke.mjs", "manual": True, "status": "BLOCKED_NATIVE_TOOLCHAIN"},
        {"phase": "desktop-smoke", "command": "LIBGL_ALWAYS_SOFTWARE=1 LUMA_SMOKE_SKIP_BUILD=1 xvfb-run -a -s '-screen 0 1920x1080x24' node tests/weather-smoke.mjs", "manual": True, "status": "BLOCKED_NATIVE_TOOLCHAIN"},
        {"phase": "desktop-smoke", "command": "LIBGL_ALWAYS_SOFTWARE=1 LUMA_SMOKE_SKIP_BUILD=1 xvfb-run -a -s '-screen 0 1920x1080x24' node tests/translations-smoke.mjs", "manual": True, "status": "BLOCKED_NATIVE_TOOLCHAIN"},
        {"phase": "optional-cross-sdk", "command": "pnpm sdk", "manual": True, "may_fetch_or_build": True, "status": "NOT_RUN"},
        {"phase": "optional-cross-build", "command": "WEBOS_NDK=\"$PWD/.build/toolchain/arm-webos-linux-gnueabi_sdk-buildroot\" pnpm build", "manual": True, "status": "NOT_RUN"},
        {"phase": "optional-cross-package", "command": "node tools/package.mjs && node tools/repository.mjs", "manual": True, "status": "NOT_RUN"},
    ]
    spec = {
        "schema": "luma-build-environment/1", "base_sha": BASE,
        "automatic_install": False, "network_requests": 0, "native_builds": 0, "device_commands": 0,
        "source_hashes": {p: sha(ROOT / p) for p in ("Cargo.toml", "Cargo.lock", "package.json", "pnpm-lock.yaml", "pnpm-workspace.yaml", "flake.nix", "flake.lock", ".github/workflows/ci.yml", "tools/build-webos.sh", "tools/setup-webos-sdk.mjs", "tools/webos-runtime.mjs")},
        "reference": {
            "preferred": "Locked Nix flake; exact system package resolution requires nix evaluation, not performed here.",
            "ci": "ubuntu-24.04; CI-equivalent apt path is not version-pinned.",
            "rust": {"ci_and_flake": re.search(r'dtolnay/rust-toolchain@([0-9.]+)', ci).group(1), "msrv": cargo["package"]["rust-version"], "components": ["rustfmt", "clippy"], "targets": ["armv7-unknown-linux-gnueabi"]},
            "node": {"ci_major": re.search(r"node-version: '([^']+)'", ci).group(1), "flake_attribute": "nodejs_24", "package_engine": package["engines"]["node"], "exact_version": "UNRESOLVED_WITHOUT_NIX_EVALUATION"},
            "pnpm": package["packageManager"],
            "flake_inputs": {name: {"rev": node["locked"]["rev"], "narHash": node["locked"]["narHash"]} for name, node in nodes.items() if "locked" in node},
            "nix_packages": ["nodejs_24", "pnpm_10", "rust-bin.stable.1.93.0", "pkg-config", "SDL2", "woff2", "python3.withPackages(fonttools)", "cmake", "git", "libGL (Linux)", "mesa (Linux)", "xvfb-run (Linux)", "util-linux (Linux)", "flock (Darwin)"],
            "ci_apt_prepare": ["libsdl2-dev", "pkg-config", "woff2", "python3-fonttools", "libgl1-mesa-dri", "xvfb", "xauth"],
            "ci_apt_smoke": ["libsdl2-2.0-0", "libgl1-mesa-dri", "xvfb", "xauth"],
            "ci_apt_cross": ["pkg-config"],
            "ci_actions": sorted(set(re.findall(r"uses:\s*([^\s]+)", ci))),
        },
        "cargo": {"lockfile_version": lock["version"], "locked_package_count": len(lock["package"]), "direct_dependencies": direct, "workspace_members": cargo["workspace"]["members"], "features": cargo["features"]},
        "node": {"dev_dependencies": package["devDependencies"], "pnpm_lockfile_version": re.search(r"lockfileVersion: '([^']+)'", text("pnpm-lock.yaml")).group(1), "only_built_dependencies": ["sharp"], "ignored_built_dependencies": ["@webos-tools/cli", "cpu-features", "ssh2"]},
        "webos": {"sdk_urls": sdk_urls, "sdk_archive_sha256": None, "sdk_archive_checksum_status": "NOT_PINNED_IN_REPOSITORY", "sdl_release": re.search(r"release = '([^']+)'", runtime).group(1), "sdl_archive_sha256": sdl_archive, "sdl_library_sha256": sdl_library, "target": "armv7-unknown-linux-gnueabi", "rustflags": "-C target-cpu=cortex-a9 -C target-feature=-neon,-soft-float", "pkg_config": "isolated PKG_CONFIG_LIBDIR=.build/sdl-webos/pkgconfig; PKG_CONFIG_PATH empty; PKG_CONFIG_SYSROOT_DIR=/"},
        "fonts": fonts,
        "expected_commands": commands,
        "do_not_run_without_separate_approval": ["pnpm deploy", "ares-install", "ares-launch", "tv/*.sh on a device", "firmware/DNS/service/compositor mutation"],
        "current_host_probe": {tool: probe(tool, args) for tool, args in [("node", ["--version"]), ("npm", ["--version"]), ("corepack", ["--version"]), ("python3", ["--version"]), ("git", ["--version"]), ("nix", ["--version"]), ("pnpm", ["--version"]), ("cargo", ["--version"]), ("rustc", ["--version"]), ("pkg-config", ["--version"]), ("sdl2-config", ["--version"]), ("cmake", ["--version"]), ("woff2_decompress", []), ("xvfb-run", ["--help"])]},
        "reproducibility_gaps": ["CI action refs are major tags, not immutable commit SHAs.", "CI apt packages and setup-node major are not exact version pins.", "Nix derivation resolution was not evaluated; flake input SHAs are pinned.", "webOS SDK archive checksum is not pinned in setup-webos-sdk.mjs.", "Current host Node 22 is not the CI/Nix Node 24 reference.", "Native Rust/Cargo/SDL/pnpm gates remain BLOCKED in this workspace."],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(spec, indent=2) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "cargo_packages": len(lock["package"]), "fonts_match": all(f["matches"] for f in fonts), "automatic_install": False}))
    return 0 if all(f["matches"] for f in fonts) else 1


if __name__ == "__main__":
    raise SystemExit(main())
