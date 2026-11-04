"""Execute an immutable 30-seed component-ablation matrix on the frozen backend."""
import argparse
from dataclasses import asdict
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import platform
import sqlite3

from integrations.salon.adapter import Adapter
from integrations.salon.checks import validate
from integrations.salon.model import Action, VARIANT_TARGET, legitimate_seeds
from integrations.salon.run import source_hashes as frozen_hashes, write
from .analysis import summarize, effects, CONTRASTS
from .experiment import campaign, replay
from .programs import MODES, bank

ROOT = Path(__file__).parents[2]

def source_hashes():
    result = frozen_hashes()
    paths = list(Path(__file__).parent.glob("*.py"))
    paths += [ROOT/"tests/test_salon_ablation.py", ROOT/"scripts/analyze_salon_ablation.py",
              ROOT/"docs/salon-ablation-protocol.md"]
    result.update({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
    return dict(sorted(result.items()))

def validate_config(c):
    if c["modes"] != list(MODES) or c["variants"] != ["fixed",*VARIANT_TARGET]:
        raise ValueError("the complete ordered treatment matrix is required")
    if c["seeds"] != list(range(600,630)):
        raise ValueError("this phase requires the frozen fresh seeds 600-629")
    if (c["budget"],c["depth"],c["corpus_capacity"]) != (120,8,64):
        raise ValueError("this phase retains the v0.5 search bounds")
    if any(isinstance(c[k],bool) for k in ("budget","depth","corpus_capacity")):
        raise ValueError("booleans are not search bounds")

def run(config_path,out):
    config_bytes = Path(config_path).read_bytes()
    config = json.loads(config_bytes)
    validate_config(config)
    output = Path(out)
    if output.exists() and any(output.iterdir()):
        raise ValueError("refusing to overwrite existing results")
    output.mkdir(parents=True,exist_ok=True)
    locked = source_hashes()
    rows,checks,costs = [],{},{}
    for variant in config["variants"]:
        adapter = Adapter(variant)
        try:
            start = adapter.http_calls
            checks[variant] = validate(adapter,variant)
            control_calls = adapter.http_calls-start
            group = []
            target = "ANY" if variant == "fixed" else VARIANT_TARGET[variant]
            start = adapter.http_calls
            for mode,seed in itertools.product(config["modes"],config["seeds"]):
                row = campaign(adapter,mode,target,seed,config["budget"],config["depth"],config["corpus_capacity"])
                row["variant"] = variant
                if variant == "fixed":
                    assert not row["detected"] and not row["other_errors"],row
                group.append(row)
                print(json.dumps({k:row[k] for k in ("variant","target","mode","seed","calls","detected")}),flush=True)
            search_http = adapter.http_calls-start
            assert search_http == sum(r["calls"]+r["shrink_calls"]+len(r["minimal_trace"]) for r in group)
            validation_calls,verified = 0,0
            for row in group:
                if not row["detected"]:
                    continue
                for key in ("trace","minimal_trace"):
                    recorded = row[key]
                    actual = replay(adapter,[Action(**s["action"]) for s in recorded],target)
                    assert actual == recorded,"witness observations changed"
                    validation_calls += len(actual)
                    verified += 1
            costs[variant] = {"authentication_calls":adapter.authentication_calls,
                "control_calls":control_calls,"campaign_calls":sum(r["calls"] for r in group),
                "shrink_calls":sum(r["shrink_calls"] for r in group),
                "post_shrink_replay_calls":sum(len(r["minimal_trace"]) for r in group),
                "validation_calls":validation_calls,"verified_witness_replays":verified,
                "all_http_calls":adapter.http_calls}
            assert adapter.http_calls == adapter.authentication_calls+control_calls+search_http+validation_calls
            rows.extend(group)
        finally:
            adapter.close()
    assert source_hashes() == locked,"source changed during the matrix"
    payload = b"".join((json.dumps(r,sort_keys=True)+"\n").encode() for r in rows)
    (output/"raw.jsonl.gz").write_bytes(gzip.compress(payload,mtime=0))
    write(output/"checks.json",checks)
    write(output/"summary.json",summarize(rows))
    write(output/"effects.json",effects(rows,config["bootstrap_samples"]))
    write(output/"manifest.json",{"phase":"v0.6 prospective component ablation",
        "config":config,"config_sha256":hashlib.sha256(config_bytes).hexdigest(),
        "source_sha256":locked,"raw_sha256":hashlib.sha256(payload).hexdigest(),
        "runs":len(rows),"costs":costs,"python":platform.python_version(),"sqlite":sqlite3.sqlite_version,
        "planned_contrasts":[list(c) for c in CONTRASTS],
        "valid_initial_bank":[[asdict(a) for a in p] for p in legitimate_seeds()],
        "random_initial_banks":{str(s):[[asdict(a) for a in p] for p in bank("mutation_unseeded",s)]
                                for s in config["seeds"]},
        "independence":"fresh search seeds on the same reviewed backend and mutants; not held-out systems",
        "control":"fixed runs ANY to monitor all oracle properties once per mode/seed"})
    print(json.dumps({"runs":len(rows),"detected":sum(r["detected"] for r in rows),
                      "all_http_calls":sum(c["all_http_calls"] for c in costs.values())}),flush=True)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config",default="configs/salon-ablation.json")
    parser.add_argument("--out",required=True)
    args = parser.parse_args()
    run(args.config,args.out)

if __name__ == "__main__":
    main()
