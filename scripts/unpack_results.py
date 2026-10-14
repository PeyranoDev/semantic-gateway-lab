"""Restore raw campaign bytes and individual witnesses from compact Git artifacts."""
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def unpack():
    validation = json.loads((ROOT / "results/release-validation.json").read_text())
    for label, recorded in validation["matrices"].items():
        folder = ROOT / "results" / label
        data = gzip.decompress((folder / "raw.jsonl.gz").read_bytes())
        if hashlib.sha256(data).hexdigest() != recorded["raw_sha256"]:
            raise ValueError(f"raw hash mismatch: {label}")
        manifest = json.loads((folder / "manifest.json").read_text())
        for name, digest in manifest["source_sha256"].items():
            if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
                raise ValueError(f"measured source hash mismatch: {name}")
        rows = [json.loads(line) for line in data.decode("utf-8").splitlines()]
        if len(rows) != recorded["runs"]:
            raise ValueError(f"run count mismatch: {label}")
        raw = folder / "raw.jsonl"
        if raw.exists() and raw.read_bytes() != data:
            raise FileExistsError(f"refusing to replace differing local results: {raw}")
        traces = folder / "traces"
        traces.mkdir(exist_ok=True)
        for row in rows:
            if row["detected"]:
                trace = traces / f"{row['mutant']}-{row['strategy']}-{row['seed']}.json"
                if trace.exists() and json.loads(trace.read_text()) != row:
                    raise FileExistsError(f"refusing to replace differing trace: {trace}")
                trace.write_text(json.dumps(row, indent=2), encoding="utf-8")
        raw.write_bytes(data)
        print(f"{label}: restored {len(rows)} runs and {sum(r['detected'] for r in rows)} traces")

if __name__ == "__main__":
    unpack()
