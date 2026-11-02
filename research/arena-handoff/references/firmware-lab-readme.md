# LG webOS firmware lab

Read-only, evidence-first research tooling for a locally extracted LG LM21ANN 03.31.82 firmware image. **This repository contains no LG firmware binaries.** Static inventory does not establish runtime call paths, rights to redistribute, or TV model compatibility.

## Two environments
- **Local Mac with authorized specimen:** run `bash scripts/run-local.sh`. The inventory is written outside this repository. Never automatically upload generated JSON, source paths or extracted code.
- **Arena/cloud agent (without specimen):** run `python3 -m unittest discover -s tests -p 'test_*.py' -v`; `python3 -m compileall -q scripts tests`. Work on synthetic fixtures only. Read [AGENTS.md](AGENTS.md) before changes.

## Inventory review
After a successful local scan:
```bash
OUT="$HOME/Projects/lg-firmware-analysis/03.31.82/cloud-evidence"
python3 scripts/verify_inventory.py "$OUT/inventory.json"
```
The verifier checks schema and highlights the v1 300-match cap, but **does not approve publication**. A human must review output for proprietary paths, model identifiers and confidential data. Do not commit raw inventory to this repo.

## Known limitations (v1)
- `matches` uses filename regexes and silently truncates each category at 300, so it is **not** a complete component count.
- `elf_headers` records header metadata, not dynamic library dependencies.
- `qml_inventory` records names and sizes, not QML behavior.
- Some paths are excluded heuristically; zero reported scanner errors does not mean complete analysis.
- Firmware-version text alone is not proof of the installed TV image/platform identity.

## Documentation map
- [docs/COUNCIL.md](docs/COUNCIL.md) — expert-council charter, evidence ladder, metrics (ICR/OC/VLC/CC/ED) and what success means.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — mermaid flows, integrity chain, trust zoning, data contracts, tool substitutions.
- [docs/PLAYBOOK.md](docs/PLAYBOOK.md) — user stories, token-efficiency rules, command atlas, failure taxonomy, skill inventory.
- [docs/STATE_OF_THE_ART.md](docs/STATE_OF_THE_ART.md) — landscape vs unblob/EMBA/FACT/OFRAK/Firmadyne et al., gap analysis, adoption decisions.
- [docs/RESEARCH.md](docs/RESEARCH.md) — vetted upstream comparison targets, multilingual research protocol, evidence levels and falsifiable milestones. REA, EMBA, FACT, Ghidra and epk2extract are **upstream references**, not vendored dependencies. Avoid unapproved downloads and heavy setup in the Arena workspace.
- [docs/CLOUD_TRANSFER.md](docs/CLOUD_TRANSFER.md) — snapshot transfer bootstrap incl. git-staging fallback.

## Development contract
One bounded change per branch; baseline test first, then changed tests, full suite, diff review and reproducible receipt. No firmware/secret uploads, device modifications or unapproved runtime experiments. See [AGENTS.md](AGENTS.md).
