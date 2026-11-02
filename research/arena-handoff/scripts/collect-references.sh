#!/usr/bin/env bash
# Read-only local reference index. No network fetch; no source/secret copy.
set -euo pipefail
[[ $# == 2 ]] || { echo 'Usage: collect-references.sh <local-clones-parent> <external-output-dir>' >&2; exit 2; }
root=$(cd "$1" && pwd -P)
mkdir -p "$2"
out=$(cd "$2" && pwd -P)
[[ "$out" != "$root" && "$out" != "$root"/* ]] || { echo 'REFUSED: output inside source root' >&2; exit 2; }
for name in lg-luma nuvio-perf-lab webos-lens LG-TV lg-webos-firmware-lab NuvioTVSmart; do
  d="$root/$name"
  [[ -d "$d/.git" ]] || { echo "MISSING $name"; continue; }
  sha=$(git -C "$d" rev-parse HEAD)
  printf '%s\t%s\n' "$name" "$sha" >> "$out/sources.tsv"
  for path in AGENTS.md README.md delivery/HANDOFF.md delivery/manifest.json lab/perf/EXPERIMENT-CLI.md docs/ARCHITECTURE.md; do
    [[ -f "$d/$path" ]] || continue
    printf '%s\t%s\t%s\n' "$name" "$sha" "$path" >> "$out/references.tsv"
  done
done
printf 'Reference index saved to %s; no source, secrets or logs copied.\n' "$out"
