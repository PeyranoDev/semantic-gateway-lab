"""python -m integrations.aoristo.run --source PATH --database-url URL --out PATH"""
import argparse
from collections import defaultdict
from dataclasses import asdict
import gzip
import hashlib
import importlib.metadata
import itertools
import json
import platform
from pathlib import Path

from fuzzlab.report import wilson
from .adapter import Adapter
from .experiment import MODES, campaign, replay
from .model import Action, PROPERTIES, SOURCE_COMMIT, legitimate_seeds
from .regressions import validate

def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True)+"\n")

def summary(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[(row["target"], row["mode"])].append(row)
    result = []
    for (target, mode), group in sorted(groups.items()):
        n, hits = len(group), sum(row["detected"] for row in group)
        interval = wilson(hits, n)
        result.append({"target": target, "mode": mode, "runs": n, "detected": hits,
                       "wilson95": interval, "mean_capped_calls": sum(r["calls"] for r in group)/n,
                       "mean_observed_states": sum(r["observed_states"] for r in group)/n})
    return result

def paired(rows):
    by = {(r["target"], r["mode"], r["seed"]): r for r in rows}
    result = []
    for target in sorted({r["target"] for r in rows}):
        left, right = "sequence_enabled", "sequence_enriched"
        seeds = sorted({r["seed"] for r in rows if r["target"] == target})
        if not all((target, mode, seed) in by for mode in (left, right) for seed in seeds):
            continue
        pairs = [(by[target, left, seed], by[target, right, seed]) for seed in seeds]
        result.append({"target": target, "left": left, "right": right,
            "seeds": seeds, "left_only": sum(a["detected"] and not b["detected"] for a,b in pairs),
            "right_only": sum(b["detected"] and not a["detected"] for a,b in pairs),
            "both": sum(a["detected"] and b["detected"] for a,b in pairs),
            "neither": sum(not a["detected"] and not b["detected"] for a,b in pairs),
            "mean_right_minus_left_capped_calls": sum(b["calls"]-a["calls"] for a,b in pairs)/len(pairs)})
    return result

def validate_config(config):
    if config.get("source_commit") != SOURCE_COMMIT:
        raise ValueError("source commit must match the source lock")
    for key in ("seeds", "modes", "properties"):
        if not config.get(key) or len(config[key]) != len(set(config[key])):
            raise ValueError("config needs distinct, nonempty "+key)
    if any(not isinstance(s, int) or isinstance(s, bool) for s in config["seeds"]):
        raise ValueError("seeds must be integers")
    if not set(config["modes"]) <= set(MODES) or not set(config["properties"]) <= set(PROPERTIES):
        raise ValueError("unknown engine or property")
    for key, minimum in (("budget", 1), ("depth", 2), ("corpus_capacity", 1)):
        value = config.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
            raise ValueError("invalid "+key)

def run(source, database_url, out, config_path):
    config_bytes = Path(config_path).read_bytes()
    config = json.loads(config_bytes)
    validate_config(config)
    output = Path(out)
    if output.exists() and any(output.iterdir()):
        raise ValueError("refusing to overwrite nonempty results directory")
    output.mkdir(parents=True, exist_ok=True)
    adapter = Adapter(source, database_url)
    try:
        regressions = validate(adapter)
        write_json(output / "regressions.json", regressions)
        print(json.dumps({"controls_passed": regressions["controls_passed"],
                          "known_witnesses_reproduced": regressions["known_witnesses_reproduced"]}), flush=True)
        rows = []
        for target, mode, seed in itertools.product(config["properties"], config["modes"], config["seeds"]):
            row = campaign(adapter, mode, target, seed, config["budget"], config["depth"], config["corpus_capacity"])
            rows.append(row)
            print(json.dumps({key: row[key] for key in ("target", "mode", "seed", "detected", "calls")}), flush=True)
        # Recheck every original and minimal witness from a clean program fixture.
        validations, validation_calls = 0, 0
        for row in rows:
            if not row["detected"]:
                continue
            for key in ("trace", "minimal_trace"):
                recorded = row[key]
                actual = replay(adapter, [Action(**step["action"]) for step in recorded], row["target"])
                validation_calls += len(actual)
                if actual != recorded:
                    raise AssertionError("witness replay changed semantic observations")
                validations += 1
        raw = b"".join((json.dumps(row, sort_keys=True)+"\n").encode() for row in rows)
        (output / "raw.jsonl.gz").write_bytes(gzip.compress(raw, mtime=0))
        write_json(output / "summary.json", summary(rows))
        write_json(output / "paired.json", paired(rows))
        source_files = sorted(Path(__file__).parent.glob("*.py"))
        manifest = {"phase": "v0.3 exploratory AoristoTech case study",
            "source": adapter.manifest, "transport": "in-process HTTP via original FastAPI ASGI pipeline",
            "database": "PostgreSQL", "schema": "original SQLAlchemy metadata.create_all; not Alembic",
            "isolation": "serial outer rollback transaction; original commits release savepoints",
            "python": platform.python_version(),
            "postgresql_version": adapter.connection.exec_driver_sql("SHOW server_version").scalar(),
            "dependencies": {d.metadata["Name"]: d.version for d in importlib.metadata.distributions()},
            "config": config, "config_sha256": hashlib.sha256(config_bytes).hexdigest(),
            "harness_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files},
            "seed_programs": [[asdict(a) for a in seed] for seed in legitimate_seeds()],
            "runs": len(rows), "campaign_calls": sum(row["calls"] for row in rows),
            "shrinking_calls": sum(row["shrink_calls"] for row in rows),
            "validation_calls": validation_calls, "witness_replays_verified": validations,
            "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "regression_calls": sum(len(r["trace"]) for k in ("controls", "known_witnesses") for r in regressions[k]),
            "not_measured": ["concurrent races", "MCP transport", "LLM agent", "live production schema",
                             "independently authored evaluation", "held-out defects"]}
        write_json(output / "manifest.json", manifest)
        report = ["# AoristoTech v0.3 exploratory results", "",
            f"Runs: {len(rows)}; campaign calls: {manifest['campaign_calls']}; verified witness replays: {validations}.",
            "", "Known defects and reviewed specification; no held-out discovery or significance claim.", "",
            "| Property | Engine | Detected | Mean capped calls |", "|---|---|---:|---:|"]
        for row in summary(rows):
            report.append(f"| {row['target']} | {row['mode']} | {row['detected']}/{row['runs']} | {row['mean_capped_calls']:.1f} |")
        report += ["", "Misses use the full call budget. Shrinking, regression and validation calls are counted separately.",
                   "The only feedback-only comparison is sequence_enabled vs sequence_enriched.",
                   "Original and minimized traces are reexecuted through the original HTTP authorization path.",
                   "This study does not demonstrate that richer feedback always improves search.", ""]
        (output / "summary.md").write_text("\n".join(report))
        print(json.dumps({"runs": len(rows), "campaign_calls": manifest["campaign_calls"],
                          "witness_replays_verified": validations, "raw_sha256": manifest["raw_sha256"]}), flush=True)
    finally:
        adapter.close()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--config", default="configs/aoristo-pilot.json")
    args = parser.parse_args()
    run(args.source, args.database_url, args.out, args.config)

if __name__ == "__main__":
    main()
