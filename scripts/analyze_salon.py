"""Verify complete matrix, source, cost accounting and every archived oracle trace offline."""
import gzip
import hashlib
import itertools
import json
from pathlib import Path
from integrations.salon.model import Action, PROPERTIES, VARIANT_TARGET, legitimate_seeds
from integrations.salon.oracle import check
from dataclasses import asdict

ROOT = Path(__file__).parents[1]

def analyze(directory=None):
    directory = Path(directory or ROOT/"results/salon-v05")
    manifest = json.loads((directory/"manifest.json").read_text())
    config = manifest["config"]
    assert hashlib.sha256((ROOT/"configs/salon-transfer.json").read_bytes()).hexdigest() == manifest["config_sha256"]
    assert config == json.loads((ROOT/"configs/salon-transfer.json").read_text())
    for path, digest in manifest["source_sha256"].items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == digest, path
    assert manifest["seed_programs"] == [[asdict(a) for a in p] for p in legitimate_seeds()]
    raw = gzip.decompress((directory/"raw.jsonl.gz").read_bytes())
    assert hashlib.sha256(raw).hexdigest() == manifest["raw_sha256"]
    rows = [json.loads(line) for line in raw.splitlines()]
    wanted = {(v,t,m,s) for v in config["variants"]
              for t in (config["properties"] if v == "fixed" else [VARIANT_TARGET[v]])
              for m,s in itertools.product(config["modes"],config["seeds"])}
    keys = {(r["variant"],r["target"],r["mode"],r["seed"]) for r in rows}
    assert len(rows) == len(keys) == manifest["runs"] == len(wanted) and keys == wanted
    for row in rows:
        assert row["detected"] == (not row["right_censored"])
        assert 1 <= row["calls"] <= config["budget"]
        for field,key in (("budget","budget"),("depth","depth")):
            assert row[field] == config[key]
        assert row["detected"] == bool(row["trace"]) == bool(row["minimal_trace"])
        if not row["detected"]:
            assert row["calls"] == config["budget"] and row["shrink_calls"] == 0
        if row["variant"] == "fixed":
            assert not row["detected"] and not row["other_errors"]
        for name in ("trace","minimal_trace"):
            trace = row[name]
            for i,step in enumerate(trace):
                action = Action(**step["action"])
                assert check(step["before"],action,step["response"],step["after"]) == step["violations"]
                if i:
                    assert trace[i-1]["after"] == step["before"]
            if trace:
                assert row["target"] in trace[-1]["violations"]
    for variant, costs in manifest["costs"].items():
        group = [r for r in rows if r["variant"] == variant]
        assert costs["campaign_calls"] == sum(r["calls"] for r in group)
        assert costs["shrink_calls"] == sum(r["shrink_calls"] for r in group)
        assert costs["post_shrink_replay_calls"] == sum(len(r["minimal_trace"]) for r in group)
        assert costs["validation_calls"] == sum(len(r["trace"])+len(r["minimal_trace"]) for r in group)
        assert costs["verified_witness_replays"] == 2*sum(r["detected"] for r in group)
        assert costs["all_http_calls"] == sum(costs[k] for k in
            ("authentication_calls","control_calls","campaign_calls","shrink_calls",
             "post_shrink_replay_calls","validation_calls"))
    checks = json.loads((directory/"checks.json").read_text())
    for variant, group in checks.items():
        assert len(group) == 12 and all(c["passed"] for c in group)
        assert manifest["costs"][variant]["control_calls"] == sum(len(c["trace"]) for c in group)
        for entry in group:
            for step in entry["trace"]:
                assert check(step["before"],Action(**step["action"]),step["response"],step["after"]) == step["violations"]
    groups = {}
    for row in rows:
        groups.setdefault((row["variant"],row["target"],row["mode"]),[]).append(row)
    summary = json.loads((directory/"summary.json").read_text())
    assert len(summary) == len(groups)
    for entry in summary:
        group = groups[entry["variant"],entry["target"],entry["mode"]]
        assert entry["runs"] == len(group) and entry["detected"] == sum(r["detected"] for r in group)
        assert entry["mean_capped_calls"] == sum(r["calls"] for r in group)/len(group)
    print(json.dumps({"verified_runs":len(rows),
                      "all_http_calls":sum(c["all_http_calls"] for c in manifest["costs"].values()),
                      "detected_mutant_campaigns":sum(r["detected"] for r in rows),
                      "fixed_campaigns":sum(r["variant"]=="fixed" for r in rows)}))
    return rows

if __name__ == "__main__":
    analyze()
