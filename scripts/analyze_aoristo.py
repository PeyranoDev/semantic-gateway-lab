"""Validate published data offline; does not replace actual PostgreSQL reexecution."""
import gzip
import hashlib
import itertools
import json
from pathlib import Path

from integrations.aoristo.model import Action
from integrations.aoristo.oracle import check
from integrations.aoristo.run import summary, paired, validate_config

def read_json(path):
    return json.loads(path.read_text())

def validate(directory):
    root = Path(__file__).parents[1]
    data = Path(directory)
    manifest = read_json(data/"manifest.json")
    config = read_json(root/"configs/aoristo-pilot.json")
    validate_config(config)
    lock = read_json(root/"integrations/aoristo/source-lock.json")
    if manifest["source_app_sha256"] != lock["app_sha256"]:
        raise AssertionError("source fingerprint changed")
    if manifest["config"] != {k:v for k,v in config.items() if k != "source_commit"}:
        raise AssertionError("campaign configuration changed")
    config_bytes = (root/"configs/aoristo-pilot.json").read_bytes()
    if hashlib.sha256(config_bytes).hexdigest() != manifest["config_sha256"]:
        raise AssertionError("config bytes changed")
    for name, digest in manifest["harness_sha256"].items():
        if hashlib.sha256((root/"integrations/aoristo"/name).read_bytes()).hexdigest() != digest:
            raise AssertionError("measured harness changed: "+name)
    dependency_bytes = (root/"integrations/aoristo/requirements.lock").read_bytes()
    if hashlib.sha256(dependency_bytes).hexdigest() != manifest["requirements_lock_sha256"]:
        raise AssertionError("dependency lock bytes changed")
    raw = gzip.decompress((data/"raw.jsonl.gz").read_bytes())
    if hashlib.sha256(raw).hexdigest() != manifest["raw_sha256"]:
        raise AssertionError("raw data hash mismatch")
    rows = [json.loads(line) for line in raw.splitlines()]
    expected = set(itertools.product(config["properties"],config["modes"],config["seeds"]))
    actual = [(r["target"],r["mode"],r["seed"]) for r in rows]
    if len(set(actual)) != len(actual) or set(actual) != expected or len(rows) != manifest["runs"]:
        raise AssertionError("missing, duplicated or extra campaigns")
    checked_steps, detections = 0, 0
    def trace_check(trace):
        nonlocal checked_steps
        for index, step in enumerate(trace):
            action = Action(**step["action"])
            if check(step["before"],action,step["response"],step["after"]) != step["violations"]:
                raise AssertionError("recorded oracle outcome changed")
            if index and trace[index-1]["after"] != step["before"]:
                raise AssertionError("trace state continuity broken")
            checked_steps += 1
    for row in rows:
        if not 1 <= row["calls"] <= config["budget"] or row["budget"] != config["budget"]:
            raise AssertionError("invalid call accounting")
        if row["right_censored"] != (not row["detected"]):
            raise AssertionError("inconsistent censoring")
        if row["detected"]:
            detections += 1
            for key in ("trace","minimal_trace"):
                trace = row[key]
                trace_check(trace)
                if not trace or not any(row["target"] in s["violations"] for s in trace):
                    raise AssertionError("target absent from witness")
        elif row["trace"] or row["minimal_trace"] or row["calls"] != row["budget"]:
            raise AssertionError("miss must consume full budget and have no target witness")
    regressions = read_json(data/"regressions.json")
    for control in regressions["controls"]:
        trace_check(control["trace"])
        if any(s["violations"] for s in control["trace"]):
            raise AssertionError("a positive/denial control failed")
    for witness in regressions["known_witnesses"]:
        trace_check(witness["trace"])
        if not any(witness["target"] in s["violations"] for s in witness["trace"]):
            raise AssertionError("known regression not reproduced")
    if summary(rows) != read_json(data/"summary.json"):
        # JSON roundtrip turns Wilson's tuple into a list.
        if json.loads(json.dumps(summary(rows))) != read_json(data/"summary.json"):
            raise AssertionError("summary mismatch")
    if paired(rows) != read_json(data/"paired.json"):
        raise AssertionError("paired summary mismatch")
    for field, observed in (("campaign_calls",sum(r["calls"] for r in rows)),
                            ("shrinking_calls",sum(r["shrink_calls"] for r in rows)),
                            ("validation_calls",sum(len(r[k]) for r in rows for k in ("trace","minimal_trace"))),
                            ("regression_calls",sum(len(r["trace"]) for k in ("controls","known_witnesses") for r in regressions[k])),
                            ("witness_replays_verified",2*detections)):
        if manifest[field] != observed:
            raise AssertionError("manifest count mismatch: "+field)
    validation = {"runs":len(rows),"detected":detections,"recorded_steps_checked":checked_steps,
                  "campaign_calls":manifest["campaign_calls"],"raw_sha256":manifest["raw_sha256"],
                  "post_shrink_trace_calls":sum(len(r["minimal_trace"]) for r in rows),
                  "total_http_calls":sum(manifest[k] for k in ("campaign_calls","shrinking_calls","validation_calls","regression_calls"))+sum(len(r["minimal_trace"]) for r in rows),
                  "offline_artifact_checks_passed":True,
                  "postgresql_reexecution": "performed by the recorded research workflow, not this script"}
    (data/"analysis-validation.json").write_text(json.dumps(validation,indent=2)+"\n")
    print(json.dumps(validation))
    return validation

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results",default="results/aoristo-v03")
    validate(parser.parse_args().results)
