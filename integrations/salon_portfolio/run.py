"""Run all 900 frozen campaigns, retaining each completed row on interruption."""
import argparse
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import platform
import sqlite3
from integrations.salon.adapter import Adapter
from integrations.salon.checks import validate
from integrations.salon.model import Action, VARIANT_TARGET
from integrations.salon.run import source_hashes as backend_hashes, write
from integrations.salon_ablation.experiment import replay
from .experiment import campaign
from .programs import MODES
from .analysis import summarize, effects

ROOT = Path(__file__).parents[2]

def source_hashes():
    result = backend_hashes()
    paths = list(Path(__file__).parent.glob("*.py"))
    paths += [ROOT/p for p in ("integrations/salon_ablation/experiment.py",
        "integrations/salon_ablation/programs.py", "integrations/salon_ablation/analysis.py",
        "fuzzlab/report.py", "tests/test_salon_portfolio.py", "scripts/verify_salon_portfolio.py",
        "docs/salon-portfolio-protocol.md", ".github/workflows/salon-portfolio.yml")]
    result.update({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
    return dict(sorted(result.items()))

def validate_config(c):
    if (c["modes"] != list(MODES) or c["variants"] != ["fixed",*VARIANT_TARGET]
        or c["seeds"] != list(range(800,830)) or c["budgets"] != [120,480]
        or c["depth"] != 8 or c["bootstrap_samples"] != 5000 or c["expected_runs"] != 900):
        raise ValueError("requires complete frozen v0.8 matrix")

def run(config_path, out):
    config_bytes = Path(config_path).read_bytes()
    config = json.loads(config_bytes)
    validate_config(config)
    output = Path(out)
    if output.exists() and any(output.iterdir()):
        raise ValueError("refusing to overwrite previous observations")
    output.mkdir(parents=True, exist_ok=True)
    locked = source_hashes()
    write(output/"started.json", {"config":config,"source_sha256":locked})
    rows, checks, costs = [], {}, {}
    with (output/"progress.jsonl").open("x") as progress:
        for variant in config["variants"]:
            adapter = Adapter(variant)
            try:
                start = adapter.http_calls
                checks[variant] = validate(adapter,variant)
                control_calls = adapter.http_calls-start
                group = []
                for budget,mode,seed in itertools.product(config["budgets"],config["modes"],config["seeds"]):
                    row = campaign(adapter,mode,seed,budget,config["depth"])
                    row["variant"] = variant
                    if variant == "fixed":
                        assert not row["detected"], row
                    group.append(row)
                    progress.write(json.dumps(row,sort_keys=True)+"\n")
                    progress.flush()
                    print(json.dumps({k:row[k] for k in ("variant","budget","mode","seed","calls","detected")}),flush=True)
                validation_calls = verified = 0
                for row in group:
                    if not row["detected"]:
                        continue
                    for field in ("trace","minimal_trace"):
                        recorded = row[field]
                        actual = replay(adapter,[Action(**s["action"]) for s in recorded],"ANY")
                        assert actual == recorded,"exact witness replay failed"
                        validation_calls += len(actual)
                        verified += 1
                costs[variant] = {"authentication_calls":adapter.authentication_calls,
                    "control_calls":control_calls,"campaign_calls":sum(r["calls"] for r in group),
                    "shrink_calls":sum(r["shrink_calls"] for r in group),
                    "post_shrink_replay_calls":sum(len(r["minimal_trace"]) for r in group),
                    "validation_calls":validation_calls,"verified_witness_replays":verified,
                    "all_http_calls":adapter.http_calls}
                assert adapter.http_calls == sum(costs[variant][k] for k in (
                    "authentication_calls","control_calls","campaign_calls","shrink_calls",
                    "post_shrink_replay_calls","validation_calls"))
                rows.extend(group)
            finally:
                adapter.close()
    assert source_hashes() == locked,"source changed during execution"
    assert len(rows) == config["expected_runs"]
    payload = (output/"progress.jsonl").read_bytes()
    (output/"raw.jsonl.gz").write_bytes(gzip.compress(payload,mtime=0))
    write(output/"checks.json",checks)
    write(output/"summary.json",summarize(rows))
    write(output/"effects.json",effects(rows,config["bootstrap_samples"]))
    write(output/"manifest.json",{"config":config,"config_sha256":hashlib.sha256(config_bytes).hexdigest(),
        "source_sha256":locked,"raw_sha256":hashlib.sha256(payload).hexdigest(),
        "runs":len(rows),"costs":costs,"python":platform.python_version(),"sqlite":sqlite3.sqlite_version,
        "transport":"FastAPI TestClient ASGI HTTP and real SQLite; no TCP in v0.8",
        "unit":"Search seed within each existing authored mutant, not independent systems"})
    # Complete raw bytes now live in the lossless compressed artifact.
    (output/"progress.jsonl").unlink()
    print(json.dumps({"runs":len(rows),"detected":sum(r["detected"] for r in rows),
                      "all_http_calls":sum(c["all_http_calls"] for c in costs.values())}),flush=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config",default="configs/salon-portfolio.json")
    parser.add_argument("--out",required=True)
    args = parser.parse_args()
    run(args.config,args.out)
