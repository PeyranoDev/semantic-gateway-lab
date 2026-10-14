"""Execute the frozen second-domain matrix; never overwrite previous results."""
import argparse
from collections import defaultdict
from dataclasses import asdict
import gzip
import hashlib
import importlib.metadata
import itertools
import json
from pathlib import Path
import platform
import sqlite3

from fuzzlab.report import wilson
from .adapter import Adapter
from .checks import validate
from .experiment import campaign, replay, MODES
from .model import Action, PROPERTIES, VARIANT_TARGET, legitimate_seeds

ROOT = Path(__file__).parents[2]

def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")

def summary(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[(row["variant"], row["target"], row["mode"])].append(row)
    return [{"variant": v, "target": t, "mode": m, "runs": len(g),
             "detected": sum(r["detected"] for r in g),
             "wilson95": wilson(sum(r["detected"] for r in g), len(g)),
             "mean_capped_calls": sum(r["calls"] for r in g) / len(g),
             "mean_observed_states": sum(r["observed_states"] for r in g) / len(g)}
            for (v, t, m), g in sorted(groups.items())]

def paired(rows):
    by = {(r["variant"], r["target"], r["mode"], r["seed"]): r for r in rows}
    result = []
    for variant, target in sorted({(r["variant"], r["target"]) for r in rows}):
        seeds = sorted({r["seed"] for r in rows if (r["variant"], r["target"]) == (variant, target)})
        pairs = [(by[variant, target, "sequence_enabled", s],
                  by[variant, target, "sequence_enriched", s]) for s in seeds]
        result.append({"variant": variant, "target": target, "seeds": seeds,
                       "left": "sequence_enabled", "right": "sequence_enriched",
                       "left_only": sum(a["detected"] and not b["detected"] for a,b in pairs),
                       "right_only": sum(b["detected"] and not a["detected"] for a,b in pairs),
                       "both": sum(a["detected"] and b["detected"] for a,b in pairs),
                       "neither": sum(not a["detected"] and not b["detected"] for a,b in pairs),
                       "mean_right_minus_left_capped_calls":
                           sum(b["calls"]-a["calls"] for a,b in pairs)/len(pairs)})
    return result

def source_hashes():
    paths = list((ROOT/"backends/salon").glob("*.py")) + list((ROOT/"integrations/salon").glob("*.py"))
    paths += [ROOT/"backends/salon/requirements.lock", ROOT/"tests/test_salon.py", ROOT/"scripts/analyze_salon.py", ROOT/"scripts/salon_http_smoke.py",
              ROOT/"fuzzlab/feedback.py", ROOT/"docs/salon-protocol.md"]
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}

def validate_config(c):
    if set(c["variants"]) != {"fixed", *VARIANT_TARGET} or len(c["variants"]) != 5:
        raise ValueError("expected all five unique variants")
    if set(c["modes"]) != set(MODES) or len(c["modes"]) != 4:
        raise ValueError("expected the four frozen engines")
    if set(c["properties"]) != set(PROPERTIES) or len(c["properties"]) != 4:
        raise ValueError("expected four properties")
    if not c["seeds"] or len(c["seeds"]) != len(set(c["seeds"])):
        raise ValueError("nonempty distinct seeds required")
    if any(not isinstance(s, int) or isinstance(s, bool) for s in c["seeds"]):
        raise ValueError("integer seeds required")
    for field, minimum in (("budget",1), ("depth",2), ("corpus_capacity",1)):
        if not isinstance(c[field], int) or isinstance(c[field], bool) or c[field] < minimum:
            raise ValueError("invalid " + field)

def run(config_path, out):
    config_bytes = Path(config_path).read_bytes()
    config = json.loads(config_bytes)
    validate_config(config)
    output = Path(out)
    if output.exists() and any(output.iterdir()):
        raise ValueError("refusing to overwrite nonempty results")
    output.mkdir(parents=True, exist_ok=True)
    rows, checks, costs = [], {}, {}
    locked = source_hashes()
    for variant in config["variants"]:
        adapter = Adapter(variant)
        try:
            start = adapter.http_calls
            checks[variant] = validate(adapter, variant)
            control_calls = adapter.http_calls-start
            start = adapter.http_calls
            group = []
            targets = config["properties"] if variant == "fixed" else [VARIANT_TARGET[variant]]
            for target, mode, seed in itertools.product(targets, config["modes"], config["seeds"]):
                row = campaign(adapter, mode, target, seed, config["budget"],
                               config["depth"], config["corpus_capacity"])
                row["variant"] = variant
                if variant == "fixed":
                    assert not row["detected"] and not row["other_errors"], row
                group.append(row)
                print(json.dumps({k:row[k] for k in
                                  ("variant","target","mode","seed","calls","detected")}), flush=True)
            search_http = adapter.http_calls-start
            assert search_http == sum(r["calls"]+r["shrink_calls"]+len(r["minimal_trace"]) for r in group)
            validation_calls = 0
            verified = 0
            for row in group:
                if not row["detected"]:
                    continue
                for key in ("trace", "minimal_trace"):
                    recorded = row[key]
                    actual = replay(adapter, [Action(**s["action"]) for s in recorded], row["target"])
                    assert actual == recorded, "witness changed on fresh fixture"
                    validation_calls += len(actual)
                    verified += 1
            costs[variant] = {
                "authentication_calls": adapter.authentication_calls,
                "control_calls": control_calls, "campaign_calls": sum(r["calls"] for r in group),
                "shrink_calls": sum(r["shrink_calls"] for r in group),
                "post_shrink_replay_calls": sum(len(r["minimal_trace"]) for r in group),
                "validation_calls": validation_calls, "verified_witness_replays": verified,
                "all_http_calls": adapter.http_calls,
            }
            assert adapter.http_calls == (adapter.authentication_calls+control_calls+search_http+validation_calls)
            rows.extend(group)
        finally:
            adapter.close()
    assert source_hashes() == locked, "source changed during experiment"
    raw = b"".join((json.dumps(row, sort_keys=True)+"\n").encode() for row in rows)
    (output/"raw.jsonl.gz").write_bytes(gzip.compress(raw, mtime=0))
    write(output/"summary.json", summary(rows))
    write(output/"paired.json", paired(rows))
    report = ["# TurnoSalon v0.5 — measured second-domain results", "",
              "Newly authored synthetic backend, isolated deliberate mutants; no independent generalization claim.", "",
              "| Variant | Property | Engine | Detected | Mean capped calls |",
              "|---|---|---|---:|---:|"]
    for entry in summary(rows):
        report.append(f"| {entry['variant']} | {entry['target']} | {entry['mode']} | "
                      f"{entry['detected']}/{entry['runs']} | {entry['mean_capped_calls']:.1f} |")
    report += ["", "Misses consume all 120 calls. Bootstrap and replay count in search budget.",
               "Shrinking, explicit controls and fresh witness verification are counted separately.",
               "Only sequence_enabled versus sequence_enriched isolates feedback.",
               "Controls with no violations do not establish general security.", ""]
    (output/"summary.md").write_text("\n".join(report))
    write(output/"checks.json", checks)
    manifest = {
        "phase": "v0.5 authored salon backend transfer", "source_sha256": locked,
        "config": config, "config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "raw_sha256": hashlib.sha256(raw).hexdigest(), "runs": len(rows), "costs": costs,
        "python": platform.python_version(), "sqlite": sqlite3.sqlite_version,
        "transport": "FastAPI ASGI via TestClient; no TCP in campaign",
        "persistence": "file-backed SQLite WAL; independent connections; committed BEGIN IMMEDIATE transactions",
        "seed_programs": [[asdict(a) for a in p] for p in legitimate_seeds()],
        "dependencies": {name: importlib.metadata.version(name) for name in
                         ("fastapi","httpx","pydantic","starlette","uvicorn")},
        "limitations": ["newly authored synthetic backend; not independent production evidence",
                        "deliberate reviewed mutants; not held-out discovery",
                        "synthetic credits, not a payment processor",
                        "finite fixture; create endpoint checked outside campaign domain",
                        "no LLM or MCP transport; SQLite concurrency differs from PostgreSQL"],
    }
    write(output/"manifest.json", manifest)
    print(json.dumps({"runs": len(rows), "all_http_calls": sum(c["all_http_calls"] for c in costs.values()),
                      "summary": summary(rows)}), flush=True)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/salon-transfer.json")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    run(args.config, args.out)

if __name__ == "__main__":
    main()
