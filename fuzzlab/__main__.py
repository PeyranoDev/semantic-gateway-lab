import argparse
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from .fuzzer import Campaign, replay
from .model import Action, MUTANTS, STRATEGIES
from .report import write_report
from .scenarios import legitimate_workflow, regression_witnesses
from .analyze import distinguishability

def main():
    parser = argparse.ArgumentParser(description="Executable authorization research laboratory")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("demo", help="show all eight synthetic regression witnesses")
    analysis = commands.add_parser("analyze", help="find a bounded abstraction counterexample")
    analysis.add_argument("--depth", type=int, default=3)
    analysis.add_argument("--out", type=Path)
    run = commands.add_parser("run", help="run a reproducible campaign matrix")
    run.add_argument("--config", type=Path, default=Path("configs/pilot.json"))
    run.add_argument("--out", type=Path, required=True)
    replay_parser = commands.add_parser("replay", help="replay a saved minimal witness")
    replay_parser.add_argument("trace", type=Path)
    args = parser.parse_args()
    if args.command == "analyze":
        payload = json.dumps(distinguishability(args.depth), indent=2)
        if args.out:
            if args.out.exists():
                parser.error("analysis output already exists")
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(payload, encoding="utf-8")
        print(payload)
        return 0
    if args.command == "demo":
        failed = False
        for mutant, (code, trace) in regression_witnesses().items():
            observation = replay(trace, mutant)
            fixed = replay(trace)
            good = code in observation["violations"] and not fixed["violations"]
            failed |= not good
            print(f"{mutant}: {'PASS' if good else 'FAIL'} ({code})")
        observation = replay(legitimate_workflow())
        failed |= bool(observation["violations"])
        print(f"legitimate_workflow: {'PASS' if not observation['violations'] else 'FAIL'}")
        return int(failed)
    if args.command == "replay":
        payload = json.loads(args.trace.read_text())
        observation = replay([Action(**a) for a in payload["minimal_trace"]], payload["mutant"])
        expected = payload["violations"][0]
        print(json.dumps(observation, indent=2))
        return int(expected not in observation["violations"])
    config = json.loads(args.config.read_text())
    seeds = config["seeds"]
    strategies, mutants = config["strategies"], config["mutants"]
    if not seeds or len(seeds) != len(set(seeds)) or any(type(s) is not int for s in seeds):
        parser.error("seeds must be unique integers")
    if not strategies or not mutants or any(s not in STRATEGIES for s in strategies):
        parser.error("invalid strategies or empty matrix")
    if any(m not in ("fixed", *MUTANTS) for m in mutants):
        parser.error("unknown mutant")
    if type(config["budget"]) is not int or type(config["depth"]) is not int or config["budget"] <= 0 or config["depth"] < 2:
        parser.error("budget must be positive and depth >= 2")
    if args.out.exists() and any(args.out.iterdir()):
        parser.error("output directory is not empty; choose a new directory to preserve prior results")
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "traces").mkdir()
    root = Path(__file__).resolve().parents[1]
    hashes = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
              for folder in ("fuzzlab", "tests") for p in sorted((root / folder).glob("*.py"))}
    manifest = {"created_utc": datetime.now(timezone.utc).isoformat(), "config": config,
                "config_sha256": hashlib.sha256(args.config.read_bytes()).hexdigest(),
                "python": sys.version, "platform": platform.platform(), "source_sha256": hashes,
                "scope": "synthetic implementation mutants; no LLM, MCP transport, or formal proof"}
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    rows = []
    with (args.out / "raw.jsonl").open("w", encoding="utf-8") as raw:
        for mutant in mutants:
            for strategy in strategies:
                for seed in seeds:
                    result = Campaign(strategy, mutant, seed, config["budget"], config["depth"]).run()
                    raw.write(json.dumps(result, sort_keys=True) + "\n")
                    raw.flush()
                    rows.append(result)
                    if result["detected"]:
                        path = args.out / "traces" / f"{mutant}-{strategy}-{seed}.json"
                        path.write_text(json.dumps(result, indent=2), encoding="utf-8")
                print(f"completed {mutant}/{strategy}", flush=True)
    write_report(rows, args.out)
    print(f"Saved {len(rows)} runs to {args.out}")
    return int(any(r["detected"] for r in rows if r["mutant"] == "fixed"))

if __name__ == "__main__":
    raise SystemExit(main())
