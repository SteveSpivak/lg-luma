#!/usr/bin/env python3
"""Deterministic pinned-source/test index and arithmetic; no native execution."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
from native_metrics import calculations

ROOT = Path(__file__).resolve().parents[2]
BASE = "e5608cd053be5376a54a806129a332952dfabcef"
HANDOFF = "0aa7bd6ac099fc457179debbf749f0227c714158"
OUT = ROOT / "research/audit"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True)


def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "merge-base", "--is-ancestor", BASE, "HEAD"], cwd=ROOT, check=True)
    paths = git("ls-tree", "-r", "--name-only", BASE).splitlines()
    source_paths = [p for p in paths if p.endswith('.rs') and p.startswith(('src/','tv-helper/','vector-geometry/','tools/vector-assets/'))]
    inventory, tests = [], []
    for path in source_paths:
        data = subprocess.check_output(["git","show",f"{BASE}:{path}"], cwd=ROOT)
        text = data.decode()
        inventory.append({"path":path,"bytes":len(data),"lines":len(text.splitlines()),"git_blob_sha1":git("rev-parse",f"{BASE}:{path}").strip(),"sha256":hashlib.sha256(data).hexdigest()})
        # Match the test attribute, not arbitrary functions or commented examples.
        for match in re.finditer(r'#\[test\]\s*(?:#\[[^\n]+\]\s*)*fn\s+([A-Za-z0-9_]+)', text):
            tests.append({"file":path,"name":match.group(1),"line":text.count('\n',0,match.start())+1,"status":"NOT_RUN","blocker":"Rust/Cargo/SDL toolchain unavailable"})
    write("source-inventory.json", {"schema":"luma-source-inventory/1","base_sha":BASE,"files":inventory})
    write("test-inventory.json", {"schema":"luma-test-inventory/1","base_sha":BASE,"count":len(tests),"method":"Static #[test] attribute inventory; cfg-gated tests included; not a cargo test listing","tests":tests})
    write("calculations.json", calculations())
    handoff_paths = git("ls-tree","-r","--name-only",HANDOFF,"--","research/arena-handoff").splitlines()
    rows=[]
    for path in handoff_paths:
        data=Path(ROOT,path).read_bytes()
        blob=hashlib.sha1(f"blob {len(data)}\0".encode()+data).hexdigest()
        rows.append({"path":path,"sha256":hashlib.sha256(data).hexdigest(),"git_blob_sha1":blob,"matches_handoff":blob==git("rev-parse",f"{HANDOFF}:{path}").strip()})
    write("handoff-integrity.json", {"schema":"luma-handoff-integrity/1","commit_sha":HANDOFF,"all_match":all(r["matches_handoff"] for r in rows),"files":rows})
    protected = [p for p in paths if p.startswith(('src/','tv-helper/','tv/','vector-geometry/','assets/','tools/','tests/')) or p in ('Cargo.toml','Cargo.lock','package.json','appinfo.json')]
    changed=[]
    for path in protected:
        before=subprocess.check_output(["git","show",f"{BASE}:{path}"],cwd=ROOT)
        if Path(ROOT,path).read_bytes()!=before: changed.append(path)
    write("source-protection.json", {"schema":"luma-source-protection/1","base_sha":BASE,"checked_files":len(protected),"changed":changed,"native_source_unchanged":not changed,"physical_tv_commands":0})
    print(json.dumps({"rust_source_files":len(inventory),"static_test_attributes":len(tests),"handoff_files":len(rows),"handoff_match":all(r['matches_handoff'] for r in rows),"protected_files_changed":changed}))
    if changed or not all(r['matches_handoff'] for r in rows): raise SystemExit(1)

if __name__ == '__main__':
    main()
