# Rendering physics and performance baseline

## Evidence status

**MEASURED in this workspace:** no native frames, GPU intervals, input-to-visible latency, GPU memory or process-memory slope. Rust/Cargo, SDL development files, pkg-config and Xvfb are absent. The standard native gates are BLOCKED. Historical TV observations in `development.md` are documentation, not measurements reproduced here.

Machine arithmetic is in `../audit/calculations.json`; it is labelled INFERRED and is not an allocation trace.

## Frame pipeline and cost ownership

1. SDL events mutate `State`; dirty scenes rebuild controls before the next input (`main.rs:1212–1218, 1510–1574`).
2. `view::scene_with_pill` allocates a command/control scene. Focus reveal may recompose once (`main.rs:437–450`).
3. `damage::Tracker::push` clones the scene into its previous-frame buffer and diffs commands. Lookahead is 8; age history is 4 (`damage.rs:8–31, 55–77`). This is O(command count) with bounded realignment, plus scene storage.
4. `Renderer::build` lays out unculled commands, tessellates first-use glyphs, loads vectors/images and uploads meshes/textures (`renderer.rs:1188–1280`).
5. `Renderer::render` clears/scissors the damage, uploads generated paint vertices and submits batches (`1285–1483`). `cpu_submission_ms` includes CPU work and GL calls, not GPU completion.
6. SDL swaps; `swap_ms` can include blocking. The profile timestamp is after the swap call, so call cadence is not an independent hardware-present timestamp (`main.rs:1770–1807`).

VSync is requested with interval 1, but success does not establish actual refresh. At 50 Hz the period is 20 ms; at 60 Hz 16.667 ms; at 120 Hz 8.333 ms. Use the observed mode plus measured cadence, not a universal 16.67 ms gate.

## Cache ledger

| Cache | Code budget / key | Ownership and limitation |
|---|---|---|
| Glyph outlines | 8 MiB or 4096 entries; `(char, font)` | CPU `Vec<Vertex>`; lazy outlines. Evicts only entries not used in current frame (`renderer.rs:21, 501–544`). |
| Text runs | 32 MiB or 512 entries; text, weight, logical layout, flags | GPU mesh payload accounting; layout reused across densities. Current-frame entries protected from eviction (`521–565, 706–932`). |
| Raster textures | 48 MiB estimated RGBA payload | GPU texture payload estimate, not driver allocation. Includes installed icons and wallpaper variants; old entries evicted after draw (`1450–1480`). |
| Vector meshes | No aggregate byte/count eviction | Individual `.lvec` validation caps 1,000,000 vertices; shared tessellator also has geometry limits. Cache can retain every loaded path (`340–345, 1038–1100`, `vector.rs`). |
| Installed artwork | 16 MiB decoded pixels / 256 entries | Separate CPU cache; thumbnails at most 256×256, 0.25 MiB each. Decode allocation limit 32 MiB; 512 KiB input file limit (`app_artwork.rs:24–29, 127–174, 647–692`). |
| Font faces | Lazy common/display/CJK/Hangul faces | Font file/face memory is outside the 8/32/48 MiB counters. Failed faces are remembered (`renderer.rs:481–499, 1718–1740`). |

The arithmetic sum 8+32+48 = **88 MiB** mixes CPU and GPU classes and is **not a GPU-memory estimate or hard process ceiling**. Active-frame overshoot, vector meshes, fonts, transient decode buffers, paint vertices, driver metadata, window buffers, MSAA and compositor copies are additional. `artwork_bytes` in diagnostics combines texture payload and vector bytes; it is not the separate CPU artwork-cache size.

### Surface arithmetic, not measured memory

Assuming two RGBA8 color buffers: 1920×1080×4×2 = **16,588,800 bytes (15.8203125 MiB)**; 3840×2160 gives **66,355,200 bytes (63.28125 MiB)**. A hypothetical four-sample color allocation multiplies those by four, but actual EGL/MSAA/AFBC/resolve allocation is driver-specific. Depth/stencil are requested as zero; compositor copies remain unknown. Do not report these as measured GPU memory. `--resolution 4k` remains experimental.

## Damage correctness and cost

- Unknown/zero age, age beyond history, drawable change and first frame draw fully. Clip/fade changes have unbounded command bounds and conservatively force full redraw.
- Text damage spans the full logical width to cover glyph overflow. A clock change can therefore redraw a full-width band; a caption weight change can do the same. This is conservative correctness, not tight damage.
- Shapes/images expand by one logical pixel; shadows include blur. Pixel conversion floors/ceilings and culling uses the expanded pixel-covered logical area, including letterboxing. Empty damage still names one inside pixel to avoid the documented Mali empty-region failure.
- `EGL_KHR_partial_update` is used when available; otherwise `EGL_EXT_buffer_age` supports scissored redraw. Non-EGL desktop contexts fall back to full redraw. `eglSetDamageRegionKHR`'s Boolean return is not checked in the current wrapper; an authorized device test should record errors/fallback rather than assume success.
- `LUMA_DAMAGE_VERIFY=1` compares partial output to a full offscreen render with a >16/channel difference threshold. Readback/FBO work makes verification mode unsuitable for performance claims. Small differences below threshold are not proof of byte identity.
- Idle `Renderer::prepare` builds another page without drawing, but advances the cache frame and can affect eviction while restoring visible-frame stats. Measure cache churn and first-navigation stalls; do not assume prewarm is free.

Existing negative tests include unknown ages, old/new shape bounds, inserted/removed rings, age unions, clip/fade invalidation, full-width text, shadow blur, low-resolution culling and nonempty inside-drawable damage (`src/damage-tests.rs`). They are **NOT_RUN**.

## Measurement gaps and proposed native protocol

Reuse `--profile-frames`, `--diagnostics`, `LUMA_PARTIAL`, `LUMA_DAMAGE_VERIFY` and `LUMA_PROFILE_SKIP`; do not add a browser/CDP collector.

Required additions before comparative claims:
- p99 nearest-rank interval alongside existing p95; preserve raw timeline and sample counts.
- Input timestamp at SDL receipt and first corresponding present call; report input-to-visible-call latency, not photons without external measurement.
- Idle wakeup/present counts over a fixed interval, with no forced redraw. Current idle waits are 100 ms normally, 250 ms hidden, 500 ms with prewarm pending, 8 ms for holds/scripts/artwork and 0 during animation/profile (`main.rs:1850–1872`). These are timeout settings, not measured wakeup rates.
- Process RSS/PSS slope where available, separated from cache payload estimates; record unavailable as null/UNKNOWN.
- Actual refresh/drawable/sample count, partial mode, buffer-age distribution, source SHA, assets hash and treatment identity.

Use the bundled lab's methodology: nearest-rank percentiles; do not call an inverted interval percentile an FPS percentile; runs/pairs are independent units, frames are not. Four A/B/B/A cycles give eight adjacent pairs as an initial protocol, not universal significance. Flag outliers/drift, reject unknown treatment identity, and keep device/memory classes separate. The bundled statistics suite itself is BLOCKED by its missing import; no upstream statistical PASS is claimed.
