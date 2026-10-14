"""Restore and verify v0.2 raw rows and derived witness files."""
import gzip
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    folder=ROOT/"results/sequence-v02"
    data=gzip.decompress((folder/"raw.jsonl.gz").read_bytes())
    validation=json.loads((folder/"validation.json").read_text())
    if hashlib.sha256(data).hexdigest()!=validation["raw_sha256"]:
        raise ValueError("raw result hash mismatch")
    manifest=json.loads((folder/"manifest.json").read_text())
    for name,digest in manifest["source_sha256"].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:
            raise ValueError(f"measured source hash mismatch: {name}")
    rows=[json.loads(line) for line in data.decode().splitlines()]
    if len(rows)!=validation["runs"]:
        raise ValueError("run count mismatch")
    raw=folder/"raw.jsonl"
    if raw.exists() and raw.read_bytes()!=data:
        raise FileExistsError("refusing to replace differing local results")
    raw.write_bytes(data)
    traces=folder/"traces"
    traces.mkdir(exist_ok=True)
    for row in rows:
        if row["detected"]:
            path=traces/f"{row['mutant']}-{row['strategy']}-{row['seed']}.json"
            if path.exists() and json.loads(path.read_text())!=row:
                raise FileExistsError(f"refusing to replace differing trace: {path}")
            path.write_text(json.dumps(row,indent=2),encoding="utf-8")
    print(f"Restored {len(rows)} runs and {sum(r['detected'] for r in rows)} witnesses")

if __name__=="__main__":
    main()
