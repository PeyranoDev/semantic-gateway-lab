"""Verify archived HTTP/SQL observations, replay pairs, request costs and hashes."""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import zipfile

from integrations.salon.model import Action
from integrations.salon.oracle import check


def analyze(output):
    output = Path(output)
    if (output/"archive.zip").is_file():
        provenance = json.loads((output/"provenance.json").read_text())
        assert hashlib.sha256((output/"archive.zip").read_bytes()).hexdigest() == provenance["artifact_sha256"]
        with TemporaryDirectory(prefix="restler-archive-") as directory:
            root = Path(directory).resolve()
            with zipfile.ZipFile(output/"archive.zip") as archive:
                for name in archive.namelist():
                    assert (root/name).resolve().is_relative_to(root), name
                archive.extractall(root)
            for name in ("summary.json", "manifest.json", "controls.json"):
                assert (output/name).read_bytes() == (root/name).read_bytes(), name
            result = analyze(root)
            if (output/"verification.json").is_file():
                assert result == json.loads((output/"verification.json").read_text())
            return result
    manifest = json.loads((output/"manifest.json").read_text())
    config = manifest["config"]
    for name, wanted in manifest["files_sha256"].items():
        assert hashlib.sha256((output/name).read_bytes()).hexdigest() == wanted, name
    rows = [json.loads(line) for line in (output/"campaigns.jsonl").read_text().splitlines()]
    expected = {(variant, mode, seed) for variant in config["variants"] for mode in config["modes"] for seed in config["seeds"]}
    assert len(rows) == len(expected)
    assert {(r["variant"], r["mode"], r["seed"]) for r in rows} == expected
    known_steps, raw_search, all_costs = 0, 0, Counter()
    for path in sorted((output/"servers").glob("*/http.jsonl.gz")):
        events = [json.loads(line) for line in gzip.open(path, "rt")]
        assert [e["event"] for e in events] == list(range(1, len(events)+1)), path
        all_costs.update(e["kind"]+":"+e.get("phase", "setup") for e in events)
        previous, sequence_calls, budget, search_calls = None, 0, 0, 0
        for e in events:
            if e["kind"] == "control" and e.get("operation") == "start":
                previous, sequence_calls, search_calls = None, 0, 0
                budget = e.get("budget", 0)
            elif e["kind"] in ("reset", "control"):
                previous, sequence_calls = None, 0
            elif e["kind"] == "http":
                if e["phase"] == "search":
                    search_calls += 1
                    raw_search += 1
                    assert e["call"] == search_calls <= budget, (path, e["event"])
                if e["action"]:
                    known_steps += 1
                    assert e["violations"] == check(e["before"], Action(**e["action"]), e["response"], e["after"])
                    if previous is not None:
                        assert e["before"] == previous, (path, e["event"], "noncontiguous SQL history")
                    previous = e["after"]
                    sequence_calls += 1
                    if e["phase"] == "search":
                        assert sequence_calls <= config["depth"], (path, e["event"], "depth exceeded")
        assert not any(e["kind"] == "infrastructure_error" for e in events), path
    assert raw_search == sum(r["calls"] for r in rows)
    summary = json.loads((output/"summary.json").read_text())
    assert summary["campaigns"] == len(rows)
    assert summary["search_calls"] == raw_search
    assert summary["revalidated_witnesses"] == sum(bool(r["replay_trace"]) for r in rows)
    for row in rows:
        assert 0 < row["calls"] <= config["budget"], row
        assert row["detected"] == bool(row["trace"]) == bool(row["replay_trace"]), row
        assert row["costs"].get("http:search", 0) == row["calls"]
        if row["variant"] == "fixed":
            assert not row["detected"], row
        if row["detected"]:
            wanted = [{k: s[k] for k in ("action", "before", "after", "response", "violations")} for s in row["trace"]]
            assert row["replay_trace"] == wanted
    for group in summary["groups"]:
        selected = [r for r in rows if r["mode"] == group["mode"] and r["variant"] == group["variant"]]
        assert group["campaigns"] == len(selected)
        assert group["detected"] == sum(r["detected"] for r in selected)
        assert group["calls"] == sum(r["calls"] for r in selected)
        assert group["stops"] == dict(Counter(r["stop"] for r in selected))
    result = {"campaigns_verified": len(rows), "search_calls_verified": raw_search,
              "oracle_steps_verified": known_steps,
              "witness_pairs_verified": summary["revalidated_witnesses"],
              "costs_all_server_events": dict(all_costs)}
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    analyze(sys.argv[1] if len(sys.argv)>1 else "results/restler-v07")
