import hashlib
import json
from pathlib import Path

CASE = Path(__file__).parents[2]/"case_studies/aoristo"

def verify_source(source, variant, private_full=False):
    root=Path(source)/"backend/app"
    lock=json.loads((CASE/"export-manifest.json").read_text())
    checked=0
    for path, entry in lock["files"].items():
        if private_full and entry["status"] != "verbatim":
            continue
        expected=(lock["patched_files"].get(path,entry["export_sha256"])
                  if variant == "fixed" else entry["export_sha256"])
        if hashlib.sha256((root/path).read_bytes()).hexdigest() != expected:
            raise ValueError("source differs from exported case: "+path)
        checked+=1
    if not private_full:
        actual={str(p.relative_to(root)) for p in root.rglob("*.py") if "__pycache__" not in p.parts}
        if actual != set(lock["files"]):
            raise ValueError("extra or missing exported source modules")
    hashes={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*.py")) if "__pycache__" not in p.parts}
    return {"variant":variant,"source_kind":"private_full" if private_full else "public_subset",
            "checked_files":checked,"app_files":len(hashes),
            "aggregate_sha256":hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()}
