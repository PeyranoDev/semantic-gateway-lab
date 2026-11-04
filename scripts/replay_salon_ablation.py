"""Reexecute all original and minimal v0.6 witnesses through the frozen HTTP/SQL API."""
from collections import defaultdict
import json
from integrations.salon.adapter import Adapter
from integrations.salon.model import Action
from integrations.salon_ablation.experiment import replay
from scripts.analyze_salon_ablation import analyze

def main():
    groups = defaultdict(list)
    for row in analyze():
        if row["detected"]:
            groups[row["variant"]].append(row)
    verified,calls = 0,0
    for variant,rows in sorted(groups.items()):
        adapter = Adapter(variant)
        try:
            for row in rows:
                for field in ("trace","minimal_trace"):
                    recorded = row[field]
                    actual = replay(adapter,[Action(**s["action"]) for s in recorded],row["target"])
                    assert actual == recorded,(variant,row["mode"],row["seed"],field)
                    calls += len(actual)
                    verified += 1
        finally:
            adapter.close()
    print(json.dumps({"verified_original_and_minimal_witnesses":verified,"replay_http_calls":calls}))

if __name__ == "__main__":
    main()
