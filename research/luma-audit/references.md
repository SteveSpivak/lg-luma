# Reference access and provenance

## Pins

| Reference | Requested SHA | Access / evidence verdict |
|---|---|---|
| Luma base | `e5608cd053be5376a54a806129a332952dfabcef` | PROVEN: checkout and GitHub commit resolve exactly; authoritative source. |
| Updated handoff | `0aa7bd6ac099fc457179debbf749f0227c714158` | PROVEN: fetched exact branch tip; all 17 extracted files match pinned Git blob IDs. |
| Nuvio performance methods | `fe27abf4df1b13cc5eb910733325db63934eb33a` | Remote BLOCKED after API 403 and git 128/HTTP403. Bundled stats/tests/known-fail snapshot is usable as a handoff-pinned snapshot, not independently verified origin content. |
| Nuvio V5 UX | `8acd6c9809adc1ecc5eb901a7e81f3596c765088` | BLOCKED / UNKNOWN implementation. No full V5 source/tests in bundle. Do not attribute upstream behavior to this pin. |
| Official NuvioTVSmart | `657c8a308d0c36aca1625a5e9293b3ba651f017b` | PROVEN commit/tree; selected source blobs verified against tree. GPL-3.0; behavior studied, no code copied. |
| webos-lens | `e5811544ec464666401e5306a420f5363076f88e` | PROVEN commit/tree. Bundled `evidence_tools.py`, `correlate.py` and evidence schema match original pinned blob IDs. |
| LG-TV contracts | `96eec049febc366eb02a97f4cf769d40fb401f22` | Remote BLOCKED after two attempts. Bundled dependency/preflight contracts are static snapshots only; underlying runtime claims not independently verified. |
| Firmware lab | `8ba1bea19743` (prefix only) | Remote BLOCKED after two attempts; full SHA UNKNOWN. Bundled README only, no specimen, ELF dependency census or binaries. |

No further requests were made to blocked repositories after the offline bundle arrived. Original API error: `Resource not accessible by integration`; git error included HTTP 403. These are access failures, not evidence that a repository or commit does not exist.

## Offline execution

`bash research/arena-handoff/scripts/verify-offline.sh` exited **1**. Python parsed both bundled Python files; four JSON documents parsed. Node failed before any statistical test assertion because `offline-lab/lab/techniques/streamMetrics.mjs` is absent. This is a bundle dependency failure, not a mathematics failure or a PASS. It was run once and not patched/retried.

The unchanged bundled evidence processor was exercised with synthetic data only: 16 research tests passed after correcting one arithmetic expectation in our new test. These cover unknown/host values, redaction, invalid environment, verified clock binding, unit/firmware mismatch, estimated-memory exclusion, unmatched IDs and fail-closed static preflight/protection rules. This is not the full upstream lens suite or full JSON-Schema validation; `jsonschema` is absent and was not installed.

**Provenance caveat:** copied `evidence_tools._commit_sha()` runs `git rev-parse HEAD` relative to this checkout. Its exported `agent.commit_sha` is therefore the Luma checkout SHA, not the lens origin SHA. Origin identity is established separately by pinned blob comparison. Do not treat the exported field as source provenance without an adapter correction in a future approved change.

The independent Python arithmetic helpers follow inspected nearest-rank semantics; they do not repair/import the broken stats bundle and do not measure rendering. Nuvio's browser layer/heap thresholds are not native Luma acceptance gates.

## Forensic reuse

- From the performance snapshot: explicit sample counts, nearest-rank intervals, run-level inference, ABBA pairing, treatment identity, drift/outlier visibility and strict known-fail accounting.
- From lens: environment and identity confidence, null rather than placeholder zero, redaction, read-only command provenance, verified same-specimen clock alignment, exact metric IDs/units and separate memory classes.
- From LG contracts: protected Home/remote/LAN/recovery functions; UNKNOWN is not verified; no disposable-service inference. The schema is a planning contract, not recovery proof.
- From firmware README: hashes/integrity before interpretation; static filenames/ELF headers/QML names do not establish runtime dependencies; scanner caps/exclusions prevent complete-inventory claims.

Raw reference metadata and selected text live outside the checkout at `/home/user/luma-research-evidence/references`. Machine-readable sanitized pins, tree/blob IDs and SHA-256 hashes are in `../audit/reference-provenance.json`; sanitized command receipts are in `../../delivery/receipts/`. No credentials, firmware archives, proprietary images, HARs or protected media were collected.
