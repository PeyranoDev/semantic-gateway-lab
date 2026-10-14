"""Public real-backend subset validation; also checks the private full fix."""
import argparse
from dataclasses import asdict
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import platform

from integrations.aoristo.experiment import campaign, replay
from integrations.aoristo.model import Action
from integrations.aoristo.regressions import validate
from integrations.aoristo.run import summary, paired
from .adapter import CaseAdapter
from .checks import fixed_checks,purchase_scope_checks,transaction_checks

ROOT=Path(__file__).parents[2]

def write(path,value):
    path.write_text(json.dumps(value,indent=2,sort_keys=True)+"\n")

def run(source,variant,database_url,out,private_full=False):
    output=Path(out)
    if output.exists() and any(output.iterdir()):
        raise ValueError("refusing to overwrite results")
    output.mkdir(parents=True,exist_ok=True)
    adapter=CaseAdapter(source,database_url,variant,private_full)
    try:
        checks=[];rows=[];historical_replays=0
        if variant=="original":
            controls=validate(adapter)
            checks.extend({"case":c["name"],"passed":True} for k in ("controls","known_witnesses") for c in controls[k])
            # Verify the extraction against all historical actual HTTP observations.
            raw=gzip.decompress((ROOT/"results/aoristo-v03/raw.jsonl.gz").read_bytes())
            for row in (json.loads(s) for s in raw.splitlines()):
                if not row["detected"]:continue
                for key in ("trace","minimal_trace"):
                    actual=replay(adapter,[Action(**s["action"]) for s in row[key]],row["target"])
                    assert actual==row[key], "Extracted backend changed historical observations"
                    historical_replays+=1
        else:
            checks.extend(fixed_checks(adapter))
            config=json.loads((ROOT/"configs/aoristo-pilot.json").read_text())
            start=adapter.http_calls
            for target,mode,seed in itertools.product(config["properties"],config["modes"],config["seeds"]):
                row=campaign(adapter,mode,target,seed,config["budget"],config["depth"],config["corpus_capacity"])
                assert not row["detected"] and not row["other_errors"],row
                rows.append(row)
                print(json.dumps({k:row[k] for k in ("target","mode","seed","calls","detected")}),flush=True)
            assert adapter.http_calls-start==sum(r["calls"]+r["shrink_calls"]+len(r["minimal_trace"]) for r in rows)
        checks.append(purchase_scope_checks(adapter,variant))
        if variant=="fixed":
            checks.extend(transaction_checks(adapter))
        payload=b"".join((json.dumps(row,sort_keys=True)+"\n").encode() for row in rows)
        (output/"raw.jsonl.gz").write_bytes(gzip.compress(payload,mtime=0))
        write(output/"summary.json",summary(rows) if rows else [])
        write(output/"checks.json",checks)
        manifest={"phase":"v0.4 public real-backend mitigation study","source":adapter.manifest,
                  "historical_original_minimal_replays":historical_replays,
                  "checks_passed":len(checks),"runs":len(rows),"campaign_calls":sum(r["calls"] for r in rows),
                  "total_http_calls":adapter.http_calls,"python":platform.python_version(),
                  "postgresql":adapter.connection.exec_driver_sql("SHOW server_version").scalar(),
                  "raw_sha256":hashlib.sha256(payload).hexdigest(),
                  "config_sha256":hashlib.sha256((ROOT/"configs/aoristo-pilot.json").read_bytes()).hexdigest(),
                  "scope":"known regressions plus finite campaign; not general security proof"}
        write(output/"manifest.json",manifest)
        print(json.dumps(manifest),flush=True)
    finally:
        adapter.close()

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",required=True)
    parser.add_argument("--variant",choices=("original","fixed"),required=True)
    parser.add_argument("--database-url",required=True)
    parser.add_argument("--out",required=True)
    parser.add_argument("--private-full",action="store_true")
    args=parser.parse_args()
    run(args.source,args.variant,args.database_url,args.out,args.private_full)
