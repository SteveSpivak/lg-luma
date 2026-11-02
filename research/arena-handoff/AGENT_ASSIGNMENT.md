# ARENA ASSIGNMENT: lg-luma Native UX and Capability Research

## Scope and fixed source
Target `SteveSpivak/lg-luma`, observed main `e5608cd053be5376a54a806129a332952dfabcef` (reverify). This is a Rust/SDL/GLES2 native launcher, not a browser/Nuvio runtime. Preserve native Home, input, audio, AirPlay/HomeKit, HDMI/CEC, Settings, updates, recovery and streaming compatibility.

Goal: evidence-led modernization of native launcher interactions and settings, plus a bounded real-video feasibility study. No proprietary Apple assets/code, DRM bypass, protected stream interception, firmware mutation, root hooks, persistent system changes, real-TV deployment, or native service changes without separate explicit authorization.

## First actions
1. Record `git status --porcelain=v2`, remote, full HEAD, branch, dependencies, Rust toolchain and packaging. Preserve dirty files. Read actual AGENTS/CLAUDE instructions.
2. Read `contracts/reference-manifest.json` in this handoff directory. Verify referenced SHAs and access. Unavailable reference is BLOCKED, not PASS.
3. Inventory existing component owners: `src/state.rs`, `src/view.rs`, `src/renderer.rs`, `src/damage.rs`, `src/egl_damage.rs`, `src/sdl_events.rs`, `src/platform.rs`, `src/recents*.rs`, `src/wallpapers*.rs`, `src/storage.rs`, `src/companion.rs`, `src/diagnostics.rs`, `src/app_artwork.rs`, `src/scroll-preview.rs`, models and tests. Reuse > adapt > create.
4. Keep desktop native, simulator and physical TV distinct.

## Research and implementation gates
**R0 Feature inventory/dependencies:** source-backed implemented/tested/measured/proposed/unknown/rejected ledger, module owners, evidence, exact test names and falsification criteria. Produce capability ledger and architecture map.

**R1 Rendering physics:** examine glyph/text/vector/texture caches and code budgets (8/32/48 MiB), damage rectangles, buffer age, redraw/scissor accuracy, image decode, CPU submission vs GPU present. Estimate upper bounds without claiming measured GPU memory. Use correct refresh-dependent frame budget (16.67 ms only for 60 Hz), p95/p99 frame intervals, input-to-visible focus, idle wakeups and memory slope. Native benchmarks, not browser layer budgets.

**R2 UI patterns:** compare Nuvio Shared Hero, card focus, trailers, progress, D-pad/Back, settings organization. Translate behavior and geometry to Luma's Rust Draw/state model; never paste CSS/DOM. One default-OFF native experiment after baseline, e.g. focus scale/depth with identical paint and hit-test geometry, settings grouping, reduced-motion fallback. Negative focus, Back, stale updates, redraw/memory tests.

**R3 Real video feasibility:** research stock platform media plane/compositor and owner-owned unprotected media routes. Compare static artwork, short decoded animation, separate supported playback app and verified hardware decoder/overlay integration. A native texture path requires proven hardware API, copies and memory limits. No real video coding/deployment without approval; avoid protected-video transforms. Deliver architecture, risk, alternative and empirical falsification plan.

**R4 Settings/companion:** audit preferences, wallpapers, recent apps, shortcuts, input labels, weather, localization, update and recovery. Preserve short-lived tokenized LAN sessions, limited interfaces, cancellation and storage migrations. Test session expiry, invalid actions, corruption and rollback. No new persistent setting without tested migration and approval.

**R5 Observability:** reuse webos-lens evidence schema with native Luma diagnostics, calibrate clock alignment; no competing collector/service. Store raw receipts outside checkout, redact identifiers; device tests NOT_RUN until authorized.

## Execution order
- Baseline `pnpm test`, `pnpm check`, `pnpm format:check`, `cargo test --locked --workspace --all-features` only when dependencies already installed; do not auto-install.
- Map owners and test baseline; compare at least two approaches for changes; avoid duplicate lifecycle owners.
- One bounded feature behind default-OFF flag, isolated Arena branch, red test first, deterministic negatives, rollback proof.
- Never change protected platform/Home code or deploy without approval.
- Targeted tests then regression/static checks; stop after two repeated failures; don't rewrite known-fail baselines to pass.

## Deliverables
Dedicated Arena branch, not main. `delivery/manifest.json` with full base/candidate SHA, SHA-256 outputs, provenance, test commands/exits and evidence labels; `delivery/HANDOFF.md`, `delivery/BLOCKERS.json`, `delivery/rollback.md`, sanitized fixtures and test receipts. Reports: capability ledger, architecture map, video feasibility, UX/settings matrix, rejected alternatives, performance baseline and one candidate patch if justified.

Evidence classes: PROVEN, OBSERVED, MEASURED, INFERRED, PROPOSED, UNKNOWN, NOT_RUN, FAIL, BLOCKED. Physical device cannot be inferred from desktop.

## Token and tool policy
Discover installed skills, MCPs, CLIs and libraries before work. Deterministic code handles Git/file search, hashes, schema validation, test execution and metrics. Smaller workers handle bounded indexing, geometry comparisons and test drafts (<=500 words plus receipt path). Stronger model resolves architectural disputes. Read narrow ranges, not entire trees or logs. No unbounded agent-generated shell or changes to source without receipts. Final response: verdict, exact SHA, files, tests, device NOT_RUN, blockers, next gate.
