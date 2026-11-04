"""Independently repeat every discovered common-oracle trace against fresh TCP/SQL."""
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import zipfile

from integrations.restler.run import TCPAdapter, start_server, terminate, revalidate


def replay_all(output):
    output = Path(output)
    if (output/"archive.zip").is_file():
        with zipfile.ZipFile(output/"archive.zip") as archive:
            rows = [json.loads(line) for line in archive.read("campaigns.jsonl").decode().splitlines()]
    else:
        rows = [json.loads(line) for line in (output/"campaigns.jsonl").read_text().splitlines()]
    count, calls = 0, 0
    with TemporaryDirectory(prefix="restler-independent-replay-") as directory:
        for variant in sorted({row["variant"] for row in rows if row["detected"]}):
            target = Path(directory)/variant
            server, log = start_server(variant, target)
            adapter = None
            try:
                adapter = TCPAdapter(target)
                for row in rows:
                    if row["variant"] == variant and row["detected"]:
                        trace = revalidate(adapter, row)
                        assert len(trace) == len(row["trace"])
                        count += 1
                        calls += len(trace)
            finally:
                if adapter:
                    adapter.close()
                terminate(server)
                log.close()
    assert count == sum(row["detected"] for row in rows)
    result = {"witnesses_replayed": count, "replay_business_calls": calls,
              "authentication_calls": 4*len({r["variant"] for r in rows if r["detected"]})}
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    replay_all(sys.argv[1] if len(sys.argv)>1 else "results/restler-v07")
