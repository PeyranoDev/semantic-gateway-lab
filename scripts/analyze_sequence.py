"""Validate v0.2 witnesses and produce descriptive paper tables."""
from collections import defaultdict
import csv
import gzip
import hashlib
import json
from pathlib import Path
import statistics
from fuzzlab.model import Action
from fuzzlab.sequence import replay_program

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/"results/sequence-v02"

def main():
    data=gzip.decompress((FOLDER/"raw.jsonl.gz").read_bytes())
    validation=json.loads((FOLDER/"validation.json").read_text())
    manifest=json.loads((FOLDER/"manifest.json").read_text())
    assert hashlib.sha256(data).hexdigest()==validation["raw_sha256"]
    for name,digest in manifest["source_sha256"].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    rows=[json.loads(line) for line in data.decode().splitlines()]
    assert len(rows)==validation["runs"]==1080
    assert len({(r["mutant"],r["strategy"],r["seed"]) for r in rows})==len(rows)
    config=manifest["config"]
    verified=0
    for row in rows:
        assert row["seed"] in config["seeds"] and row["strategy"] in config["strategies"]
        assert row["mutant"] in config["mutants"]
        assert row["budget"]==config["budget"] and row["max_depth"]==config["depth"]
        assert row["calls"]==row["allowed"]+row["denied"]<=row["budget"]
        assert row["right_censored"]==(not row["detected"])
        if row["detected"]:
            original=replay_program([Action(**a) for a in row["trace"]],row["mutant"])
            minimal=replay_program([Action(**a) for a in row["minimal_trace"]],row["mutant"])
            target=row["violations"][0]
            assert target in original["violations"] and target in minimal["violations"]
            assert original["before"]==row["witness"]["before"]
            assert original["after"]==row["witness"]["after"]
            assert original["response"]==row["witness"]["response"]
            assert not replay_program([Action(**a) for a in row["minimal_trace"]])["violations"]
            assert row["calls"]==row["first_failure_call"]
            verified+=1
        else:
            assert row["calls"]==row["budget"] and row["first_failure_call"] is None
    assert verified==validation["verified_witnesses"]
    controls=[r for r in rows if r["mutant"]=="fixed"]
    assert len(controls)==90 and not any(r["detected"] for r in controls)
    grouped=defaultdict(list)
    for row in rows:
        grouped[row["mutant"],row["strategy"]].append(row)
    diagnostics=[]
    for strategy in config["strategies"]:
        selected=grouped["fixed",strategy]
        sequence=[r for r in selected if r["strategy"].startswith("sequence_")]
        diagnostics.append({"strategy":strategy,"control_runs":len(selected),
            "mean_concrete_states":statistics.mean(r["concrete_states"] for r in selected),
            "mean_abstract_states":statistics.mean(r["abstract_states"] for r in selected),
            "mean_corpus_evictions":statistics.mean(r["corpus_evictions"] for r in sequence) if sequence else None,
            "mean_corpus_program_length":statistics.mean(r["corpus_mean_program_length"] for r in sequence) if sequence else None,
            "mean_source_prefix_fraction":statistics.mean(r["source_prefix_calls"]/r["calls"] for r in sequence) if sequence else None,
            "mean_noop_mutation_fraction":statistics.mean(r["noop_mutations"]/r["mutations"] for r in sequence) if sequence else None})
    with (FOLDER/"control-diagnostics.csv").open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(diagnostics[0]))
        writer.writeheader();writer.writerows(diagnostics)
    primary=("enabled","sequence_uniform","sequence_enabled","sequence_enriched")
    labels=("Legacy enabled","Seed mutation, no corpus","Seed mutation, coarse","Seed mutation, enriched")
    lines=["# Sequence-mutation follow-up: measured results v0.2","",
        f"{len(rows)} runs; {sum(r['calls'] for r in rows):,} executed backend calls; "
        f"{verified} original/minimized witnesses replayed by the separate analysis step.",
        "65 automated tests passed on Python 3.11, 3.12 and 3.13 before the matrix.",
        "The 90 fixed-control campaigns produced zero observed violations (270,000 calls).","",
        "All results are from a synthetic service. Ten seeds per condition yield substantial uncertainty; "
        "full Wilson intervals and matched descriptions are stored with the raw data.",
        "First-failure stopping and censored misses remain part of the analysis.","",
        "## Detection fractions","",
        "| Variant | "+" | ".join(labels)+" |","|---|"+"---:|"*len(primary)]
    for variant in config["mutants"]:
        cells=[]
        for strategy in primary:
            group=grouped[variant,strategy]
            cells.append(f"{sum(r['detected'] for r in group)}/{len(group)}")
        lines.append("| "+variant+" | "+" | ".join(cells)+" |")
    lines+=["","## Mean capped call effort","",
        "Misses contribute the full 3000-call budget. Bootstrap and repeated calls count. "
        "This is a descriptive capped-effort metric, not an uncensored estimate.",
        "","| Variant | "+" | ".join(labels)+" |","|---|"+"---:|"*len(primary)]
    for variant in ("approval_replay","sharing_overwrite","wrong_recipient"):
        cells=[]
        for strategy in primary:
            group=grouped[variant,strategy]
            effort=statistics.mean(r["first_failure_call"] if r["detected"] else r["budget"] for r in group)
            cells.append(f"{effort:.1f}")
        lines.append("| "+variant+" | "+" | ".join(cells)+" |")
    lines+=["","## Paired contrasts and ablations","",
        "The CSV includes all nine engines; paired.json retains same-seed discordant detections "
        "and capped-effort differences. A positive right-minus-left difference means more calls "
        "for the right-hand treatment. No significance or optimality claim is made.","",
        "| Variant | Contrast | Left-only hits | Right-only hits | Mean right-minus-left calls |",
        "|---|---|---:|---:|---:|"]
    pairs=json.loads((FOLDER/"paired.json").read_text())
    for pair in pairs:
        if pair["mutant"] in ("approval_replay","sharing_overwrite","wrong_recipient"):
            lines.append(f"| {pair['mutant']} | {pair['contrast']} | {pair['left_only']} | "
                         f"{pair['right_only']} | {pair['mean_capped_call_difference_right_minus_left']:.1f} |")
    lines+=["","## Corpus diagnostics at equal full budget","",
        "Only fixed-control runs are used, so all treatments execute the full budget. "
        "Legacy selected-prefix replay and new unchanged-source-prefix calls differ and are not pooled.",
        "","| Sequence engine | Mean stored keys | Mean evictions | Mean program length | Source-prefix calls | No-op mutations |",
        "|---|---:|---:|---:|---:|---:|"]
    for d in diagnostics:
        if d["strategy"].startswith("sequence_"):
            lines.append(f"| {d['strategy']} | {d['mean_abstract_states']:.1f} | "
                f"{d['mean_corpus_evictions']:.1f} | {d['mean_corpus_program_length']:.1f} | "
                f"{d['mean_source_prefix_fraction']:.1%} | {d['mean_noop_mutation_fraction']:.1%} |")
    lines+=["","## Interpretation","",
        "Workflow-seeded mutation makes approval reuse discoverable in this benchmark. "
        "That comparison changes both initial workflow knowledge and mutation, so it does not isolate "
        "a mutation-only benefit against v0.1. The matched new corpus engines share both.",
        "",
        "Enrichment is property-dependent: it lowers observed approval-replay call effort relative "
        "to the coarse key, while coarse guidance is faster for sharing overwrite. Removing approval "
        "history changes those costs in opposite directions. The no-corpus seed mutator is competitive, "
        "showing that much of the gain can come from seeds and mutations without richer feedback.",
        "",
        "Wrong-recipient discovery regresses relative to legacy guidance. The new engine is not "
        "a universal replacement. Stored-program sampling and argument-distribution effects "
        "require further controlled ablations before causal mechanisms are asserted.",
        "",
        "Approval replay here relies on deleting and recreating the same identifier. The fixture "
        "does not model generation/version binding. This is a narrow test of consumed-grant history, "
        "not evidence of the same vulnerability in systems with non-reused identifiers.",
        "",
        "Reserved variants were authored in the same project and backend. They support within-project "
        "extension, not independent external generalization. No LLM or actual MCP transport is evaluated.",
        "",
        "## Reproduce","",
        "Source experiment commit: ab4b6c3388b54d1efb021fc7ee9afecf59309805.",
        "Experiment run: https://github.com/PeyranoDev/semantic-gateway-lab/actions/runs/38593192649",
        "",chr(96)*3+"bash","python scripts/unpack_sequence_results.py",
        "python -m fuzzlab.sequence run --config configs/sequence-pilot.json --out results/local-sequence",
        "python -m scripts.analyze_sequence",chr(96)*3,"",
        "Fresh output reproduces the configured matrix; timings vary by machine. "
        "The analysis command regenerates tables from the committed historical dataset.",""]
    (ROOT/"paper/sequence-results.md").write_text("\n".join(lines),encoding="utf-8")
    result={"runs":len(rows),"raw_sha256":validation["raw_sha256"],"source_hashes_verified":True,
            "original_witnesses_replayed":verified,"minimal_witnesses_replayed":verified,
            "fixed_minimal_replays_checked":verified,"fixed_violations":0}
    (FOLDER/"analysis-validation.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print("SEQUENCE_ANALYSIS="+json.dumps(result,sort_keys=True),flush=True)

if __name__=="__main__":
    main()
