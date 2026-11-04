"""Check source hashes, complete matrix, scheduling, statistics and live replays."""
from collections import defaultdict
from dataclasses import asdict
import argparse
import gzip
import hashlib
import itertools
import json
from pathlib import Path
from integrations.salon.model import Action
from integrations.salon.oracle import check
from integrations.salon_ablation.experiment import replay
from integrations.salon_portfolio.programs import Scheduler
from integrations.salon_portfolio.analysis import summarize, effects
from integrations.salon_portfolio.run import ROOT, source_hashes, validate_config

def verify_ledger(row):
    scheduler = Scheduler(row["mode"],row["seed"],row["depth"])
    calls = bootstrap_calls = 0
    ledger = row["episode_ledger"]
    assert len(ledger) == row["episodes"]
    for index,entry in enumerate(ledger):
        arm,program,bootstrap,operator = scheduler.next()
        assert (arm,bootstrap,operator) == (entry["arm"],entry["bootstrap"],entry["operator"])
        executed = entry["calls"]
        assert 1 <= executed <= min(len(program),row["budget"]-calls)
        if index < len(ledger)-1 or not row["detected"]:
            assert executed == min(len(program),row["budget"]-calls)
        elif row["detected"]:
            assert [asdict(a) for a in program[:executed]] == [s["action"] for s in row["trace"]]
        scheduler.charge(arm,executed)
        calls += executed
        bootstrap_calls += int(bootstrap)*executed
        if row["mode"] == "portfolio_balanced":
            assert abs(scheduler.calls["random"]-scheduler.calls["sequence_uniform"]) <= row["depth"]
    assert scheduler.calls == row["arm_calls"]
    assert calls == row["calls"] and bootstrap_calls == row["bootstrap_calls"]

def verify(directory, live=False):
    output = Path(directory)
    manifest = json.loads((output/"manifest.json").read_text())
    c = manifest["config"]
    validate_config(c)
    assert c == json.loads((ROOT/"configs/salon-portfolio.json").read_text())
    assert hashlib.sha256((ROOT/"configs/salon-portfolio.json").read_bytes()).hexdigest() == manifest["config_sha256"]
    assert source_hashes() == manifest["source_sha256"]
    payload = gzip.decompress((output/"raw.jsonl.gz").read_bytes())
    assert hashlib.sha256(payload).hexdigest() == manifest["raw_sha256"]
    rows = [json.loads(line) for line in payload.splitlines()]
    expected = set(itertools.product(c["variants"],c["budgets"],c["modes"],c["seeds"]))
    assert len(rows) == len(expected) == manifest["runs"] == c["expected_runs"]
    assert {(r["variant"],r["budget"],r["mode"],r["seed"]) for r in rows} == expected
    checks = json.loads((output/"checks.json").read_text())
    assert set(checks) == set(c["variants"])
    for variant,controls in checks.items():
        assert len(controls) == 12 and all(e["passed"] for e in controls)
        assert manifest["costs"][variant]["control_calls"] == sum(len(e["trace"]) for e in controls)
        for entry in controls:
            for s in entry["trace"]:
                assert check(s["before"],Action(**s["action"]),s["response"],s["after"]) == s["violations"]
    for r in rows:
        assert r["target"] == "ANY" and r["depth"] == c["depth"]
        assert r["detected"] == bool(r["trace"]) == bool(r["minimal_trace"]) == (not r["right_censored"])
        assert 1 <= r["calls"] <= r["budget"]
        if not r["detected"]:
            assert r["calls"] == r["budget"] and r["shrink_calls"] == 0
        if r["variant"] == "fixed":
            assert not r["detected"]
        verify_ledger(r)
        for field in ("trace","minimal_trace"):
            trace = r[field]
            for i,s in enumerate(trace):
                assert check(s["before"],Action(**s["action"]),s["response"],s["after"]) == s["violations"]
                if i:
                    assert trace[i-1]["after"] == s["before"]
                if i < len(trace)-1:
                    assert not s["violations"]
            if trace:
                assert trace[-1]["violations"]
    for variant,costs in manifest["costs"].items():
        group = [r for r in rows if r["variant"] == variant]
        assert costs["campaign_calls"] == sum(r["calls"] for r in group)
        assert costs["shrink_calls"] == sum(r["shrink_calls"] for r in group)
        assert costs["post_shrink_replay_calls"] == sum(len(r["minimal_trace"]) for r in group)
        assert costs["validation_calls"] == sum(len(r["trace"])+len(r["minimal_trace"]) for r in group)
        assert costs["verified_witness_replays"] == 2*sum(r["detected"] for r in group)
        assert costs["all_http_calls"] == sum(costs[k] for k in (
            "authentication_calls","control_calls","campaign_calls","shrink_calls",
            "post_shrink_replay_calls","validation_calls"))
    assert json.loads((output/"summary.json").read_text()) == summarize(rows)
    assert json.loads((output/"effects.json").read_text()) == effects(rows,c["bootstrap_samples"])
    live_count = live_calls = 0
    if live:
        from integrations.salon.adapter import Adapter
        for variant in c["variants"]:
            adapter = Adapter(variant)
            try:
                for row in rows:
                    if row["variant"] != variant or not row["detected"]:
                        continue
                    for field in ("trace","minimal_trace"):
                        recorded = row[field]
                        assert replay(adapter,[Action(**s["action"]) for s in recorded],"ANY") == recorded
                        live_count += 1
                        live_calls += len(recorded)
            finally:
                adapter.close()
    result = {"verified_runs":len(rows),"detected_campaigns":sum(r["detected"] for r in rows),
              "search_calls":sum(r["calls"] for r in rows),
              "all_http_calls":sum(c["all_http_calls"] for c in manifest["costs"].values()),
              "live_witness_replays":live_count,"live_replay_calls":live_calls}
    print(json.dumps(result,sort_keys=True))
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory",nargs="?",default="results/salon-v08")
    parser.add_argument("--replay",action="store_true")
    args = parser.parse_args()
    verify(args.directory,args.replay)
