#!/usr/bin/env python3
"""Standalone offline wrapper for Nuvio/GHUI and webos-lens correlation.

Example:
  python3 cli/correlate.py --device lens-evidence.json --browser browser-receipt.json \
      --alignment time-alignment.json --out combined.json
"""
import argparse
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from evidence_tools import correlate


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--device", required=True, help="webos-lens normalized evidence JSON")
    p.add_argument("--browser", required=True, help="Nuvio/GHUI browser performance receipt JSON")
    p.add_argument("--alignment", required=True, help="explicit user-supplied clock-alignment JSON")
    p.add_argument("--out", default="correlation.json")
    a = p.parse_args()
    try:
        result = correlate(a.device, a.browser, a.alignment)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as e:
        p.error("invalid input: %s" % e)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write("\n")
    print("correlation -> %s" % a.out)
    return 0

if __name__ == "__main__":
    sys.exit(main())
