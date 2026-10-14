"""Check that the verifier-only repair changed no measured semantic campaign field."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]

def check(record=False):
    main = ROOT/"results/salon-v06"
    first = main/"intermediate/attempt1"
    manifests = [json.loads((d/"manifest.json").read_text()) for d in (first,main)]
    raw = [gzip.decompress((d/"raw.jsonl.gz").read_bytes()) for d in (first,main)]
    for payload,manifest in zip(raw,manifests):
        assert hashlib.sha256(payload).hexdigest() == manifest["raw_sha256"]
    assert manifests[0]["config"] == manifests[1]["config"]
    assert manifests[0]["config_sha256"] == manifests[1]["config_sha256"]
    assert manifests[0]["costs"] == manifests[1]["costs"]
    before,after = (m["source_sha256"] for m in manifests)
    assert set(before) == set(after)
    changed = sorted(p for p in before if before[p] != after[p])
    assert changed == ["integrations/salon_ablation/analysis.py","tests/test_salon_ablation.py"]
    matrices = [[json.loads(s) for s in payload.splitlines()] for payload in raw]
    assert len(matrices[0]) == len(matrices[1]) == 1200
    for left,right in zip(*matrices):
        left.pop("elapsed_s")
        right.pop("elapsed_s")
        assert left == right,(left["variant"],left["mode"],left["seed"])
    for filename in ("summary.json","effects.json","checks.json"):
        assert json.loads((first/filename).read_text()) == json.loads((main/filename).read_text())
    expected = {"semantic_rows_compared":1200,"semantic_rows_equal":1200,
        "ignored_fields":["elapsed_s"],"changed_source_paths":changed,
        "first_measurement_commit":"011359225b375b485afcf53aea518db9efaa760e",
        "corrected_measurement_commit":"6f9f0b359cde92dc1bd694ea1a279fc04e02173f",
        "config_sha256":manifests[1]["config_sha256"],
        "raw_sha256_attempt1":manifests[0]["raw_sha256"],
        "raw_sha256_canonical":manifests[1]["raw_sha256"],
        "primary_http_calls":sum(c["all_http_calls"] for c in manifests[1]["costs"].values()),
        "attempt1_http_calls":sum(c["all_http_calls"] for c in manifests[0]["costs"].values()),
        "replication_note":"verifier-only rerun; attempts are not pooled as independent samples"}
    proof = main/"repair-verification.json"
    if record and not proof.exists():
        proof.write_text(json.dumps(expected,sort_keys=True,indent=2)+"\n")
    else:
        assert json.loads(proof.read_text()) == expected
    print(json.dumps(expected))
    return expected

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record",action="store_true")
    check(parser.parse_args().record)
