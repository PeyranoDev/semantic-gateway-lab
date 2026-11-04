"""Offline verification of v0.6 source identity, complete treatments and paired effects."""
from dataclasses import asdict
import gzip
import hashlib
import itertools
import json
from pathlib import Path

from integrations.salon.model import Action, VARIANT_TARGET, legitimate_seeds
from integrations.salon.oracle import check
from integrations.salon_ablation.analysis import CONTRASTS, summarize, effects
from integrations.salon_ablation.programs import bank, bank_digest

ROOT = Path(__file__).parents[1]

def analyze(directory=None):
    directory = Path(directory or ROOT/"results/salon-v06")
    manifest = json.loads((directory/"manifest.json").read_text())
    config = json.loads((ROOT/"configs/salon-ablation.json").read_text())
    assert config == manifest["config"]
    assert hashlib.sha256((ROOT/"configs/salon-ablation.json").read_bytes()).hexdigest() == manifest["config_sha256"]
    for path,digest in manifest["source_sha256"].items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == digest,path
    assert manifest["planned_contrasts"] == [list(c) for c in CONTRASTS]
    assert manifest["valid_initial_bank"] == [[asdict(a) for a in p] for p in legitimate_seeds()]
    for seed in config["seeds"]:
        assert manifest["random_initial_banks"][str(seed)] == [[asdict(a) for a in p]
                                                             for p in bank("mutation_unseeded",seed)]
    payload = gzip.decompress((directory/"raw.jsonl.gz").read_bytes())
    assert hashlib.sha256(payload).hexdigest() == manifest["raw_sha256"]
    rows = [json.loads(s) for s in payload.splitlines()]
    wanted = {(v,"ANY" if v == "fixed" else VARIANT_TARGET[v],m,s)
              for v,m,s in itertools.product(config["variants"],config["modes"],config["seeds"])}
    keys = {(r["variant"],r["target"],r["mode"],r["seed"]) for r in rows}
    assert len(rows) == len(keys) == len(wanted) == manifest["runs"] == config["expected_runs"]
    assert keys == wanted
    checks = json.loads((directory/"checks.json").read_text())
    assert set(checks) == set(config["variants"])
    for variant,group in checks.items():
        assert len(group) == 12 and all(c["passed"] for c in group)
        assert manifest["costs"][variant]["control_calls"] == sum(len(c["trace"]) for c in group)
        for case in group:
            for step in case["trace"]:
                assert check(step["before"],Action(**step["action"]),step["response"],step["after"]) == step["violations"]
    for row in rows:
        assert row["initial_bank_sha256"] == bank_digest(bank(row["mode"],row["seed"]))
        assert row["budget"] == config["budget"] and row["depth"] == config["depth"]
        assert 1 <= row["calls"] <= row["budget"] and row["right_censored"] == (not row["detected"])
        assert row["detected"] == bool(row["trace"]) == bool(row["minimal_trace"])
        assert 0 <= row["bootstrap_calls"] <= min(24,row["calls"])
        if row["mode"] == "random":
            assert row["bootstrap_calls"] == 0
        if not row["detected"]:
            assert row["calls"] == row["budget"] and row["shrink_calls"] == 0
        if row["variant"] == "fixed":
            assert not row["detected"] and not row["other_errors"]
        for name in ("trace","minimal_trace"):
            trace = row[name]
            for index,step in enumerate(trace):
                assert check(step["before"],Action(**step["action"]),step["response"],step["after"]) == step["violations"]
                if index:
                    assert trace[index-1]["after"] == step["before"]
            if trace:
                assert row["target"] in trace[-1]["violations"]
    for variant,costs in manifest["costs"].items():
        group = [r for r in rows if r["variant"] == variant]
        assert costs["campaign_calls"] == sum(r["calls"] for r in group)
        assert costs["shrink_calls"] == sum(r["shrink_calls"] for r in group)
        assert costs["post_shrink_replay_calls"] == sum(len(r["minimal_trace"]) for r in group)
        assert costs["validation_calls"] == sum(len(r["trace"])+len(r["minimal_trace"]) for r in group)
        assert costs["verified_witness_replays"] == 2*sum(r["detected"] for r in group)
        assert costs["all_http_calls"] == sum(costs[k] for k in ("authentication_calls","control_calls",
            "campaign_calls","shrink_calls","post_shrink_replay_calls","validation_calls"))
    assert json.loads((directory/"summary.json").read_text()) == summarize(rows)
    assert json.loads((directory/"effects.json").read_text()) == effects(rows,config["bootstrap_samples"])
    result = {"verified_runs":len(rows),"detected_campaigns":sum(r["detected"] for r in rows),
              "all_http_calls":sum(c["all_http_calls"] for c in manifest["costs"].values()),
              "paired_contrasts":len(CONTRASTS)*len(VARIANT_TARGET)}
    print(json.dumps(result))
    return rows

if __name__ == "__main__":
    analyze()
