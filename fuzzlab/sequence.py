"""Versioned sequence campaigns; v0.1 modules remain byte-for-byte unchanged."""
import argparse
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import platform
import random
import statistics
import sys
import time
from unittest.mock import patch

from .abstraction import concrete_key
from .feedback import Corpus, program_key, project
from .fuzzer import Campaign, minimize, replay
from .model import Action, MUTANTS, canonical
from .mutation import SequenceMutator, legitimate_seeds
from .oracle import inspect
from .report import summarize, write_report
from .reserved import RESERVED, gateway

SEQUENCE_MODES = {
    "sequence_uniform": (None, "uniform"),
    "sequence_enabled": ("enabled", "rare"),
    "sequence_enriched": ("enriched", "rare"),
    "sequence_no_recipient": ("no_recipient", "rare"),
    "sequence_no_approval": ("no_approval", "rare"),
    "sequence_no_owner": ("no_owner", "rare"),
    "sequence_enriched_uniform": ("enriched", "uniform"),
}
ALL_STRATEGIES = ("random", "enabled", "enriched", *SEQUENCE_MODES)

def replay_program(actions, variant="fixed"):
    # Injection point is confined to the single-threaded evaluation harness.
    # The frozen legacy implementation and independent oracle are not edited.
    with patch("fuzzlab.fuzzer.Gateway", gateway):
        return replay(actions, variant)

class SequenceCampaign:
    def __init__(self, strategy="sequence_enabled", mutant="fixed", seed=0,
                 budget=3000, depth=20, capacity=64):
        if strategy not in SEQUENCE_MODES or mutant not in ("fixed", *MUTANTS, *RESERVED):
            raise ValueError("unknown strategy or variant")
        if type(seed) is not int or type(budget) is not int or budget <= 0 or depth < 2:
            raise ValueError("invalid campaign parameters")
        self.strategy, self.mutant, self.seed = strategy, mutant, seed
        self.budget, self.depth = budget, depth
        self.rng = random.Random(seed)
        self.mode, scheduler = SEQUENCE_MODES[strategy]
        self.corpus = Corpus(capacity, scheduler)
        self.mutator = SequenceMutator(self.rng, depth)

    def run(self):
        started = time.perf_counter()
        seeds = [program[:self.depth] for program in legitimate_seeds()]
        seed_queue = list(seeds)
        spent = bootstrap_calls = prefix_calls = episodes = allowed = denied = 0
        mutations = noops = 0
        operator_counts = Counter()
        states, edges, abstract_edges = set(), set(), set()
        latencies = []
        trace, failure, witness = [], [], None
        first_step, discovery_phase = None, None
        initial = gateway(self.mutant).state.snapshot()
        states.add(concrete_key(initial))
        while spent < self.budget and not failure:
            is_bootstrap = bool(seed_queue)
            if is_bootstrap:
                candidate = list(seed_queue.pop(0))
                source, common_prefix = [], 0
            else:
                source = (self.corpus.select(self.rng) if self.mode and self.corpus.entries
                          and self.rng.random() < .8 else list(self.rng.choice(seeds)))
                donor = self.rng.choice(seeds)
                candidate, operator = self.mutator.mutate(source, donor)
                operator_counts[operator] += 1
                mutations += 1
                noops += int(candidate == source)
                common_prefix = 0
                for old, new in zip(source, candidate):
                    if old != new:
                        break
                    common_prefix += 1
            service = gateway(self.mutant)
            episodes += 1
            sequence, feedback = [], []
            for index, action in enumerate(candidate):
                if spent >= self.budget:
                    break
                before = service.state.snapshot()
                t0 = time.perf_counter_ns()
                response = service.execute(action)
                latencies.append(time.perf_counter_ns() - t0)
                after = service.state.snapshot()
                spent += 1
                bootstrap_calls += int(is_bootstrap)
                prefix_calls += int(not is_bootstrap and index < common_prefix)
                allowed += int(response["allowed"])
                denied += int(not response["allowed"])
                sequence.append(action)
                old, new = concrete_key(before), concrete_key(after)
                states.add(new)
                edges.add((old, action.tool, response["allowed"], new))
                if self.mode:
                    edge = (project(before, self.mode), action.tool, response["allowed"],
                            project(after, self.mode))
                    abstract_edges.add(edge)
                    feedback.append(canonical(edge))
                failure = inspect(before, action, response, after)
                if failure:
                    first_step, trace = spent, list(sequence)
                    discovery_phase = "bootstrap" if is_bootstrap else "mutation"
                    witness = {"before": before, "after": after, "response": response}
                    break
            if not failure and self.mode:
                # Archive complete tested programs, not unexecuted suffixes.
                for key in feedback:
                    self.corpus.remember(key, sequence)
        elapsed = time.perf_counter() - started
        with patch("fuzzlab.fuzzer.Gateway", gateway):
            shrunk, shrink_calls = minimize(trace, self.mutant, failure[0]) if failure else ([], 0)
        timings = sorted(latencies)
        return {"strategy": self.strategy, "mutant": self.mutant, "seed": self.seed,
                "budget": self.budget, "max_depth": self.depth, "calls": spent,
                "replay_calls": prefix_calls, "replay_definition": "unchanged_mutation_source_prefix",
                "source_prefix_calls": prefix_calls, "bootstrap_calls": bootstrap_calls,
                "episodes": episodes, "allowed": allowed, "denied": denied,
                "detected": bool(failure), "first_failure_call": first_step,
                "right_censored": not bool(failure), "violations": failure,
                "discovery_phase": discovery_phase, "mutations": mutations,
                "noop_mutations": noops, "operator_counts": dict(sorted(operator_counts.items())),
                "elapsed_s": elapsed, "gateway_p95_us": timings[int((len(timings)-1)*.95)]/1000,
                "concrete_states": len(states), "concrete_edges": len(edges),
                "abstract_states": len(self.corpus.entries) if self.mode else 0,
                "abstract_edges": len(abstract_edges), "corpus_evictions": self.corpus.evictions,
                "corpus_mean_program_length": (statistics.mean(map(len,self.corpus.entries.values()))
                                               if self.mode and self.corpus.entries else 0),
                "trace": [asdict(a) for a in trace], "minimal_trace": [asdict(a) for a in shrunk],
                "witness": witness, "shrink_calls": shrink_calls,
                "coverage_digest": hashlib.sha256(canonical(sorted(edges)).encode()).hexdigest()}

def run_campaign(strategy, mutant, seed, budget, depth, capacity=64):
    if strategy in ("random", "enabled", "enriched"):
        with patch("fuzzlab.fuzzer.Gateway", gateway):
            result = Campaign(strategy, mutant, seed, budget, depth).run()
        result.update(replay_definition="legacy_selected_corpus_prefix", bootstrap_calls=0,
                      source_prefix_calls=None, discovery_phase="legacy",
                      mutations=None, noop_mutations=None, operator_counts={},
                      corpus_evictions=None, corpus_mean_program_length=None)
        return result
    return SequenceCampaign(strategy, mutant, seed, budget, depth, capacity).run()

def paired_description(rows, out):
    by_key = {(r["mutant"], r["strategy"], r["seed"]): r for r in rows}
    pairs = []
    mutants = sorted({r["mutant"] for r in rows})
    contrasts = [
        ("sequence_enabled", "sequence_enriched", "abstraction"),
        ("sequence_uniform", "sequence_enabled", "corpus_guidance"),
        ("sequence_enriched", "sequence_no_recipient", "recipient_ablation"),
        ("sequence_enriched", "sequence_no_approval", "approval_ablation"),
        ("sequence_enriched", "sequence_enriched_uniform", "scheduler_ablation"),
    ]
    for mutant in mutants:
        for left, right, label in contrasts:
            values = []
            for seed in sorted({r["seed"] for r in rows}):
                a, b = by_key.get((mutant,left,seed)), by_key.get((mutant,right,seed))
                if a and b:
                    effort_a = a["first_failure_call"] if a["detected"] else a["budget"]
                    effort_b = b["first_failure_call"] if b["detected"] else b["budget"]
                    values.append((a,b,effort_b-effort_a))
            if values:
                pairs.append({"mutant":mutant, "contrast":label, "left":left, "right":right,
                              "pairs":len(values),
                              "both_detect":sum(a["detected"] and b["detected"] for a,b,_ in values),
                              "left_only":sum(a["detected"] and not b["detected"] for a,b,_ in values),
                              "right_only":sum(b["detected"] and not a["detected"] for a,b,_ in values),
                              "neither":sum(not a["detected"] and not b["detected"] for a,b,_ in values),
                              "mean_capped_call_difference_right_minus_left":
                                  statistics.mean(delta for _,_,delta in values)})
    (out/"paired.json").write_text(json.dumps(pairs,indent=2),encoding="utf-8")
    return pairs

def main():
    parser = argparse.ArgumentParser(description="Versioned sequence mutation experiments")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--config", type=Path, default=Path("configs/sequence-pilot.json"))
    run.add_argument("--out", type=Path, required=True)
    play = sub.add_parser("replay")
    play.add_argument("trace",type=Path)
    args = parser.parse_args()
    if args.command == "replay":
        data = json.loads(args.trace.read_text())
        result = replay_program([Action(**a) for a in data["minimal_trace"]],data["mutant"])
        print(json.dumps(result,indent=2))
        return int(data["violations"][0] not in result["violations"])
    config = json.loads(args.config.read_text())
    seeds, strategies, variants = config["seeds"], config["strategies"], config["mutants"]
    if not seeds or len(seeds)!=len(set(seeds)) or any(type(s) is not int for s in seeds):
        parser.error("seeds must be unique integers")
    if not strategies or len(strategies)!=len(set(strategies)) or any(s not in ALL_STRATEGIES for s in strategies):
        parser.error("invalid strategies")
    if not variants or len(variants)!=len(set(variants)) or any(m not in ("fixed",*MUTANTS,*RESERVED) for m in variants):
        parser.error("invalid variants")
    if type(config["budget"]) is not int or config["budget"]<=0 or type(config["depth"]) is not int or config["depth"]<2:
        parser.error("invalid budget/depth")
    if args.out.exists() and any(args.out.iterdir()):
        parser.error("output directory is not empty")
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"traces").mkdir()
    root=Path(__file__).resolve().parents[1]
    hashes={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in ("fuzzlab","tests") for p in sorted((root/folder).glob("*.py"))}
    manifest={"created_utc":datetime.now(timezone.utc).isoformat(),"config":config,
              "config_sha256":hashlib.sha256(args.config.read_bytes()).hexdigest(),
              "python":sys.version,"platform":platform.platform(),"source_sha256":hashes,
              "seed_programs_sha256":hashlib.sha256(canonical([[asdict(a) for a in p]
                  for p in legitimate_seeds()]).encode()).hexdigest(),
              "scope":"synthetic variants; original baselines unchanged; no LLM; descriptive comparison"}
    (args.out/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    rows=[]
    for variant in variants:
        for strategy in strategies:
            for seed in seeds:
                result=run_campaign(strategy,variant,seed,config["budget"],config["depth"],config.get("capacity",64))
                if result["detected"]:
                    actions=[Action(**a) for a in result["minimal_trace"]]
                    observed=replay_program(actions,variant)
                    if result["violations"][0] not in observed["violations"]:
                        raise RuntimeError("minimized witness does not replay")
                    if replay_program(actions)["violations"]:
                        raise RuntimeError("fixed control disagrees with oracle")
                    result["witness_verified"]=True
                    path=args.out/"traces"/f"{variant}-{strategy}-{seed}.json"
                    path.write_text(json.dumps(result,indent=2),encoding="utf-8")
                rows.append(result)
            print(f"completed {variant}/{strategy}",flush=True)
    raw="".join(json.dumps(r,sort_keys=True)+"\n" for r in rows).encode()
    (args.out/"raw.jsonl.gz").write_bytes(gzip.compress(raw,mtime=0))
    write_report(rows,args.out)
    paired_description(rows,args.out)
    metadata={"runs":len(rows),"backend_calls":sum(r["calls"] for r in rows),
              "fixed_runs":sum(r["mutant"]=="fixed" for r in rows),
              "fixed_violations":sum(r["detected"] for r in rows if r["mutant"]=="fixed"),
              "verified_witnesses":sum(r["detected"] for r in rows),
              "raw_sha256":hashlib.sha256(raw).hexdigest()}
    (args.out/"validation.json").write_text(json.dumps(metadata,indent=2),encoding="utf-8")
    print("SEQUENCE_VALIDATION="+json.dumps(metadata,sort_keys=True),flush=True)
    print("SEQUENCE_SUMMARY="+json.dumps(summarize(rows),sort_keys=True),flush=True)
    return int(metadata["fixed_violations"]!=0)

if __name__ == "__main__":
    raise SystemExit(main())
