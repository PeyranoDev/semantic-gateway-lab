"""Reexecute every archived witness against its pinned HTTP/SQL variant."""
import json
from collections import defaultdict
from integrations.salon.adapter import Adapter
from integrations.salon.model import Action
from integrations.salon.experiment import replay
from scripts.analyze_salon import analyze

def main():
    groups = defaultdict(list)
    for row in analyze():
        if row["detected"]:
            groups[row["variant"]].append(row)
    count, calls = 0, 0
    for variant, rows in sorted(groups.items()):
        adapter = Adapter(variant)
        try:
            for row in rows:
                for field in ("trace","minimal_trace"):
                    recorded = row[field]
                    actual = replay(adapter,[Action(**step["action"]) for step in recorded],row["target"])
                    assert actual == recorded, (variant,row["mode"],row["seed"],field)
                    count += 1
                    calls += len(actual)
        finally:
            adapter.close()
    print(json.dumps({"verified_original_and_minimal_witnesses":count,"replay_http_calls":calls}))

if __name__ == "__main__":
    main()
