# Self-contained offline reference pack (2026-11-02)

The original handoff listed remote references but did not actually include them. These copied text artifacts now remove that dependency for a **bounded initial source audit**.

| Local file | Origin and immutable ref | Purpose |
|---|---|---|
| `references/nuvio-perf-stats.mjs` | `SteveSpivak/nuvio-perf-lab@fe27abf4df1b13cc5eb910733325db63934eb33a:lab/perf/stats.mjs` | Statistical semantics (native Luma still needs its own instrumented collection) |
| `references/nuvio-known-fail-signatures.json` | same SHA: `lab/checks/known-fail-signatures.json` | Example of strict failure-drift accounting, not a Luma baseline |
| `references/lg-feature-dependencies.json` | `SteveSpivak/LG-TV@96eec049febc366eb02a97f4cf769d40fb401f22:LG-TV/contracts/feature-dependencies.json` | Protected features and static dependency warnings |
| `references/lg-device-preflight.schema.json` | same LG-TV SHA: `LG-TV/contracts/device-preflight.schema.json` | Device-readiness schema; cannot prove physical recovery |
| `references/firmware-lab-readme.md` | `SteveSpivak/lg-webos-firmware-lab@8ba1bea19743:README.md` | Specimen limitations and offline forensic methodology; **not** full firmware inventory |
| `references/lens-evidence.schema.json` | `SteveSpivak/webos-lens@e5811544ec464666401e5306a420f5363076f88e:contracts/lens-evidence.schema.json` | Normalized observation contract |

These are **reference snapshots**, not Luma source modules. Do not import `nuvio-perf-stats.mjs` into the production Rust launcher or treat its browser-specific metrics as measured native timings. Do not run device operations or include credentials.

## Agent: revised execution contract

1. **Do not retry inaccessible companion repositories**; the two-failure stop is respected. Use bundled references first. Note unavailable details as UNKNOWN.
2. **No Rust/Cargo/pnpm/SDL/Xvfb**: run source/static audits, existing dependency-free Node checks, pure offline statistical tests where possible; mark native build/renderer/device tests BLOCKED, never PASS. Do not auto-install dependencies.
3. **Deliver source-backed artifacts even when toolchains are absent:** Rust component-owner graph, feature ledger with original files and paths, memory/frame-budget calculations with assumptions, card/focus UX test contracts, settings audit, media-plane option matrix, falsification criteria and risk-ranked next experiments.
4. Use original `AGENT_ASSIGNMENT.md` for architecture and protected-feature requirements, but **this local pack supersedes its assumption that external repositories are reachable**.
5. If visual behavior or native implementation needs actual on-device verification, stop at the explicit device approval gate. Do not rewrite Luma to fake a successful measurement.

## Still not included

Full Nuvio V5 app source and tests, detailed firmware ELF inventory, full LG-TV recovery scripts, complete webos-lens correlation CLI and any hardware sample. Their absence must be recorded accurately. These are **not necessary** for the first bounded native Luma audit; request specific missing evidence for later tasks rather than fetching entire repositories.
