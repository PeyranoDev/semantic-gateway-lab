"""Offline integrity checks for the public real-backend original/fixed results."""
import gzip
import hashlib
import itertools
import json
from pathlib import Path

from integrations.aoristo.run import summary
from integrations.aoristo_case.provenance import CASE

def validate():
    root=Path(__file__).parents[1]
    export=json.loads((CASE/"export-manifest.json").read_text())
    config_bytes=(root/"configs/aoristo-pilot.json").read_bytes()
    config=json.loads(config_bytes)
    results=[]
    for variant in ("original","fixed"):
        folder=root/"results"/f"aoristo-v04-{variant}"
        manifest=json.loads((folder/"manifest.json").read_text())
        checks=json.loads((folder/"checks.json").read_text())
        assert len(checks)==manifest["checks_passed"] and all(c["passed"] for c in checks)
        hashes={p:(export["patched_files"].get(p,e["export_sha256"]) if variant=="fixed" else e["export_sha256"])
                for p,e in export["files"].items()}
        aggregate=hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()
        assert aggregate==manifest["source"]["aggregate_sha256"]
        assert hashlib.sha256(config_bytes).hexdigest()==manifest["config_sha256"]
        raw=gzip.decompress((folder/"raw.jsonl.gz").read_bytes())
        assert hashlib.sha256(raw).hexdigest()==manifest["raw_sha256"]
        rows=[json.loads(line) for line in raw.splitlines()]
        assert len(rows)==manifest["runs"]
        if variant=="original":
            assert not rows and manifest["historical_original_minimal_replays"]==150
            assert manifest["checks_passed"]==19 and manifest["total_http_calls"]==288
        else:
            identities=[(r["target"],r["mode"],r["seed"]) for r in rows]
            expected=set(itertools.product(config["properties"],config["modes"],config["seeds"]))
            assert len(set(identities))==len(identities) and set(identities)==expected
            assert len(rows)==120 and manifest["campaign_calls"]==14400
            assert all(not r["detected"] and not r["other_errors"] and r["calls"]==r["budget"]==120 for r in rows)
            assert json.loads(json.dumps(summary(rows)))==json.loads((folder/"summary.json").read_text())
            concurrent=next(c for c in checks if c["case"].startswith("concurrent-http"))
            assert concurrent["statuses"]==[200,400] and concurrent["stock_after"]==10
        results.append({"variant":variant,"checks_passed":len(checks),"runs":len(rows),
                        "total_http_calls":manifest["total_http_calls"],"integrity_passed":True})
    print(json.dumps(results))
    return results

if __name__=="__main__":validate()
