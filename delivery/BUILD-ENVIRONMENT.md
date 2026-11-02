# Minimal reproducible build environment (manual only)

**Base:** `e5608cd053be5376a54a806129a332952dfabcef`. Machine-readable derivation: `build-environment.json`. **Nothing was installed, downloaded, built or deployed while preparing this specification.** Native gates remain BLOCKED here.

## Preferred reference: locked Nix shell

`flake.nix` + `flake.lock` are the closest existing reproducible specification:

| Input/tool | Exact declared pin |
|---|---|
| nixpkgs | `5adc50831c259f87faeb09ddf930d43597197473`; narHash `sha256-Q/8KLB6jNfpaUN1HAedE/u/Et9feE/zYSsutBLKrCFk=` |
| rust-overlay | `83dd732f2428827f35d997deae108a2ced5125f4`; narHash `sha256-mrM+zFDRO1pI85t2SEq5R739BIq7Nv5XkFtVZK9nkZM=` |
| Rust | `1.93.0`, components `rustfmt`, `clippy`; target `armv7-unknown-linux-gnueabi` |
| Rust MSRV | `1.88` (minimum, not the CI reference) |
| Node | `nodejs_24`; exact derivation version requires Nix evaluation, not performed here |
| pnpm | `10.34.5` from `packageManager`; flake asserts `pnpm_10.version` matches |
| Other Nix packages | `pkg-config`, `SDL2`, `woff2`, Python 3 + `fonttools`, `cmake`, `git`; Linux: `libGL`, `mesa`, `xvfb-run`, `util-linux`; Darwin: `flock` |

Manual command: `nix develop`. Nix is absent in this workspace; no evaluation/fetch was attempted.

## CI-equivalent Ubuntu path

CI runner: `ubuntu-24.04`; Node major `24`; pnpm from `packageManager`; Rust `1.93.0`.

- Prepare/build apt packages: `libsdl2-dev pkg-config woff2 python3-fonttools libgl1-mesa-dri xvfb xauth`.
- Smoke-only runtime packages: `libsdl2-2.0-0 libgl1-mesa-dri xvfb xauth`.
- Cross-build host package: `pkg-config`, plus the webOS SDK below.
- CI actions are declared as major tags (`actions/checkout@v7`, `pnpm/action-setup@v6`, `actions/setup-node@v7`, `dtolnay/rust-toolchain@1.93.0`, `Swatinem/rust-cache@v2`, upload/download artifact `v7`/`v8`), not immutable action SHAs.

**Reproducibility limit:** apt package versions and Node `24` are not exact pins in CI. Prefer the locked flake for a reference environment; record actual resolved versions before any performance comparison. Current host Node `v22.22.3` satisfies `package.json` engines but is **not** the CI/Nix Node 24 reference.

## Exact application dependencies

Cargo lock: version 4, **116 locked package entries**, SHA-256 in `build-environment.json`. Direct locked versions:

| Crate | Locked | Crate | Locked |
|---|---:|---|---:|
| getrandom | 0.2.17 | gl | 0.14.0 |
| if-addrs | 0.14.0 | image | 0.25.10 |
| libc | 0.2.191 | owned_ttf_parser | 0.25.1 |
| qrcodegen | 1.8.0 | ring | 0.17.14 |
| sdl2 | 0.38.0 | serde | 1.0.229 |
| serde_json | 1.0.154 | time | 0.3.55 |
| ureq | 3.5.0 | lyon_tessellation | 1.0.23 |
| usvg | 0.45.1 | local workspace crates | 0.1.0 |

Node lock: `pnpm-lock.yaml` lockfile version `9.0`. Exact dev dependencies: `@changesets/cli 3.0.3`, `@webos-tools/cli 3.2.6`, `oxfmt 0.73.0`, `oxlint 1.88.0`, `sharp 0.35.5`. Only `sharp` is allowed to run build scripts; `@webos-tools/cli`, `cpu-features`, `ssh2` are explicitly ignored for builds. Use `pnpm install --frozen-lockfile`; do not substitute npm or regenerate locks.

Bundled Noto fonts are present and match their source pins: SC `a3041811…f0da`, KR `194018e6…e252`, OFL `1c05c68c…7d9` (full hashes in JSON). `pnpm assets` needs `woff2_decompress`, Python/fontTools and sharp. `pnpm assets:fonts` is a manual network fallback only if those files are missing; it was not run.

## webOS cross-build inputs (optional, not device deployment)

- SDK release tags: Linux x64 `openlgtv/buildroot-nc4` `webos-b17b4cc`; macOS/ARM64 Linux `webosbrew/native-toolchain` `webos-d7ed7ee.6`. Exact URLs are in JSON. **The SDK archive checksum is not pinned in the repository**; compiler version/archive hash must be recorded after an approved manual setup.
- SDL-webOS `release-2.30.12-webos.5`; archive SHA-256 `4ad566453d113bdd9ee96878176b97d28d9fa70503a62d83d55a351545abb334`; library SHA-256 `f564f7da624cec47168300d017f3ec822f41b5096f0ce1c96873eecd8614d446`.
- Preserve `tools/build-webos.sh`: gnueabi soft-float ABI, Cortex-A9/VFP flags `-C target-cpu=cortex-a9 -C target-feature=-neon,-soft-float`, explicit sysroot, isolated `PKG_CONFIG_LIBDIR=.build/sdl-webos/pkgconfig`, empty `PKG_CONFIG_PATH`, `PKG_CONFIG_SYSROOT_DIR=/`. Do not use host SDL or generic bundled SDL for TV.

## Expected manual command sequence

```sh
# Reference environment and dependencies: manual, may fetch/build.
nix develop
pnpm install --frozen-lockfile

# Desktop gates. pnpm test includes Cargo; do not call a Node subset a full PASS.
pnpm format:check
pnpm check
pnpm test
pnpm assets
cargo build --locked --package luma --no-default-features

# CI-equivalent isolated desktop smoke, after assets/build exist.
export LIBGL_ALWAYS_SOFTWARE=1 LUMA_SMOKE_SKIP_BUILD=1
xvfb-run -a -s '-screen 0 1920x1080x24' node tests/smoke.mjs
xvfb-run -a -s '-screen 0 1920x1080x24' node tests/brands-smoke.mjs
xvfb-run -a -s '-screen 0 1920x1080x24' node tests/weather-smoke.mjs
xvfb-run -a -s '-screen 0 1920x1080x24' node tests/translations-smoke.mjs

# Optional cross-build/package only; no deployment.
pnpm sdk
export WEBOS_NDK="$PWD/.build/toolchain/arm-webos-linux-gnueabi_sdk-buildroot"
pnpm build
node tools/package.mjs
node tools/repository.mjs
```

Do **not** run `pnpm deploy`, `ares-install`, `ares-launch`, TV shell scripts on a device, or firmware/DNS/service/compositor mutations without separate approval. No library upgrades are justified by this audit; keep the existing locks unchanged.
