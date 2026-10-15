"""Execute a pinned official RESTler build and our generators against one TCP harness."""
import argparse
from collections import Counter
from dataclasses import asdict
import gzip
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import uuid

import httpx
from backends.salon.db import Database
from integrations.salon.model import ACTORS, Action
from integrations.salon.checks import validate
from integrations.salon_ablation.experiment import campaign, replay
from .spec import RESTLER_COMMIT, write_inputs

ROOT = Path(__file__).resolve().parents[2]


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True)+"\n")


class TCPAdapter:
    def __init__(self, output, port=8765):
        self.output = Path(output)
        self.client = httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=20, trust_env=False)
        self.database = Database(self.output/"salon.db")
        self.headers = {"anonymous": {}}
        self.sequence = str(uuid.uuid4())
        for actor in ACTORS:
            if actor == "anonymous":
                continue
            response = self.client.post("/sessions", json={"username": actor, "password": "research-only-"+actor})
            response.raise_for_status()
            self.headers[actor] = {"Authorization": "Bearer "+response.json()["access_token"]}

    def start(self, phase, budget=0):
        response = self.client.post("/_lab/start", json={"phase": phase, "budget": budget})
        response.raise_for_status()

    def status(self):
        return json.loads((self.output/"status.json").read_text())

    def reset(self):
        # The campaign's post-detection minimization/revalidation is a separate cost.
        if self.status()["phase"] == "search" and self.status()["stopped"]:
            self.start("replay")
        self.sequence = str(uuid.uuid4())
        self.client.post("/_lab/reset", headers={"x-lab-sequence": self.sequence}).raise_for_status()

    def snapshot(self):
        return self.database.snapshot()

    def execute(self, action):
        path = "/bookings" if action.operation == "list_bookings" else "/bookings/"+action.resource
        if action.operation not in ("list_bookings", "read_booking"):
            path += "/"+action.operation
        response = self.client.request("GET" if action.operation in ("list_bookings", "read_booking") else "POST",
               path, headers={**self.headers[action.actor], "x-lab-sequence": self.sequence})
        return {"status": response.status_code, "body": response.json()}

    def close(self):
        self.client.close()


def terminate(process):
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)


def start_server(variant, output):
    output.mkdir(parents=True, exist_ok=True)
    log = (output/"server.log").open("w")
    process = subprocess.Popen([sys.executable, "-m", "integrations.restler.server", "--variant", variant,
                                "--out", str(output)], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                               start_new_session=True)
    try:
        deadline = time.monotonic()+30
        with httpx.Client(timeout=1, trust_env=False) as client:
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError("observation server exited: "+(output/"server.log").read_text())
                try:
                    if client.get("http://127.0.0.1:8765/health").status_code == 200:
                        return process, log
                except httpx.HTTPError:
                    pass
                time.sleep(.05)
        raise RuntimeError("observation server readiness timed out")
    except BaseException:
        terminate(process)
        log.close()
        raise


def journal(output):
    return [json.loads(line) for line in (Path(output)/"http.jsonl").read_text().splitlines()]


def characterize(events):
    http = [e for e in events if e["kind"] == "http" and e["phase"] == "search"]
    faults = [e for e in http if e["violations"]]
    first = faults[0] if faults else None
    trace = [e for e in http if first and e["episode"] == first["episode"] and e["event"] <= first["event"]]
    return {"calls": len(http), "detected": bool(first), "violations": first["violations"] if first else [],
            "trace": trace, "routes": dict(Counter(e["method"]+" "+e["path"] for e in http)),
            "statuses": dict(Counter(str(e["status"]) for e in http)),
            "successful_operations": sorted({e["action"]["operation"] for e in http if e["action"] and e["status"] == 200}),
            "outside_domain": sum(e["domain"] == "outside" for e in http),
            "costs": dict(Counter(e["kind"]+":"+e.get("phase", "setup") for e in events))}


def restler_run(executable, compiled, directory, mode, seed, config, adapter):
    directory.mkdir(parents=True, exist_ok=True)
    settings = {"fuzzing_mode": mode, "max_sequence_length": config["depth"],
                "max_combinations": config["max_combinations"], "random_seed": seed,
                "generate_random_seed": False, "fuzzing_jobs": 1,
                "include_unique_sequence_id": True, "reconnect_on_every_request": False,
                "sequence_exploration_settings": {"create_prefix_once": []},
                "garbage_collection_interval": None, "garbage_collector_cleanup_time": 0,
                "max_request_execution_time": 10, "no_tokens_in_logs": True,
                "global_producer_timing_delay": 0}
    write_json(directory/"settings.json", settings)
    command = [str(executable), "fuzz", "--grammar_file", str(compiled/"grammar.py"),
               "--dictionary_file", str(compiled/"dict.json"), "--settings", str(directory/"settings.json"),
               "--target_ip", "127.0.0.1", "--target_port", "8765", "--no_ssl", "--disable_checkers", "*",
               "--time_budget", str(config["wall_timeout_seconds"]/3600)]
    with (directory/"driver.log").open("w") as log:
        process = subprocess.Popen(command, cwd=directory, stdout=log, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        deadline = time.monotonic()+config["wall_timeout_seconds"]
        stop = None
        while process.poll() is None:
            status = adapter.status()
            if status["infrastructure_errors"]:
                stop = "infrastructure_error"
                break
            if status["stopped"]:
                stop = "oracle_violation"
                break
            if status["calls"] >= config["budget"]:
                stop = "budget"
                break
            if time.monotonic() >= deadline:
                stop = "wall_timeout"
                break
            time.sleep(.01)
        natural_exit = process.poll()
        terminate(process)
    if stop is None:
        stop = "natural_completion" if natural_exit == 0 else "tool_error"
    write_json(directory/"invocation.json", {"command": command, "stop": stop,
                 "natural_exit_code": natural_exit, "final_exit_code": process.returncode})
    return stop


def official_smoke(executable, compiled, directory, adapter):
    directory.mkdir(parents=True, exist_ok=True)
    adapter.start("validation")
    offset = len(journal(adapter.output))
    settings = {"max_combinations": 25, "include_unique_sequence_id": True,
                "sequence_exploration_settings": {"create_prefix_once": []},
                "garbage_collector_cleanup_time": 0, "max_request_execution_time": 10}
    write_json(directory/"settings.json", settings)
    command = [str(executable), "test", "--grammar_file", str(compiled/"grammar.py"),
               "--dictionary_file", str(compiled/"dict.json"), "--settings", str(directory/"settings.json"),
               "--target_ip", "127.0.0.1", "--target_port", "8765", "--no_ssl", "--disable_checkers", "*"]
    with (directory/"driver.log").open("w") as log:
        result = subprocess.run(command, cwd=directory, stdout=log, stderr=subprocess.STDOUT, timeout=90)
    events = journal(adapter.output)[offset:]
    http = [e for e in events if e["kind"] == "http"]
    write_json(directory/"observation.json", {"command": command, "exit_code": result.returncode,
               "http_calls": len(http), "outside_domain": sum(e["domain"] == "outside" for e in http),
               "successful_operations": sorted({e["action"]["operation"] for e in http if e["action"] and e["status"] == 200}),
               "statuses": dict(Counter(str(e["status"]) for e in http)),
               "infrastructure_errors": adapter.status()["infrastructure_errors"]})
    if result.returncode or adapter.status()["infrastructure_errors"] or not http:
        raise AssertionError("official RESTler smoke failed; retain artifacts and repair setup")


def revalidate(adapter, observation):
    if not observation["trace"]:
        return []
    if any(e["action"] is None for e in observation["trace"]):
        raise AssertionError("outside-domain witness cannot be silently normalized")
    adapter.start("replay")
    program = [Action(**e["action"]) for e in observation["trace"]]
    trace = replay(adapter, program, "ANY")
    wanted = [{k: e[k] for k in ("action", "before", "after", "response", "violations")}
              for e in observation["trace"]]
    if trace != wanted:
        raise AssertionError("TCP witness changed on independent replay")
    return trace


def scrub(output, replacements):
    """Keep native reports and compiler grammar, with ephemeral session values replaced."""
    for path in output.rglob("*"):
        if not path.is_file() or path.suffix in (".db", ".gz", ".pyc", ".dll", ".pdb") or "__pycache__" in path.parts:
            continue
        try:
            original = path.read_text()
        except UnicodeError:
            continue
        modified = original
        for token, actor in replacements.items():
            modified = modified.replace(token, "<fixture-session:"+actor+">")
        if modified != original:
            path.write_text(modified)
    for path in output.rglob("salon.db*"):
        path.unlink()
    for path in output.rglob("__pycache__"):
        import shutil
        shutil.rmtree(path)


def run(executable, upstream, output, config_path):
    config_path = Path(config_path).resolve()
    config = json.loads(config_path.read_text())
    actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=upstream, text=True).strip()
    if actual != RESTLER_COMMIT or config["restler_commit"] != actual:
        raise AssertionError("RESTler source is not the pinned official commit")
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=upstream, text=True).strip():
        raise AssertionError("official RESTler checkout has modifications")
    output = Path(output).resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError("output must be empty to preserve earlier attempts")
    output.mkdir(parents=True, exist_ok=True)
    rows, controls, tokens = [], [], {}
    compiled = None
    started = time.time()
    try:
        for variant in config["variants"]:
            server_output = output/"servers"/variant
            server, log = start_server(variant, server_output)
            adapter = None
            try:
                adapter = TCPAdapter(server_output)
                tokens.update({h["Authorization"][7:]: a for a, h in adapter.headers.items() if h})
                adapter.start("validation")
                controls.append({"variant": variant, "checks": validate(adapter, variant)})
                if compiled is None:
                    compiler = write_inputs(output/"inputs", adapter.headers)
                    compile_dir = output/"compile"
                    compile_dir.mkdir()
                    with (compile_dir/"driver.log").open("w") as compiler_log:
                        subprocess.run([str(executable), "compile", str(compiler)], cwd=compile_dir,
                                       stdout=compiler_log, stderr=subprocess.STDOUT, check=True, timeout=120)
                    compiled = compile_dir/"Compile"
                    if not (compiled/"grammar.py").is_file():
                        raise AssertionError("official compiler produced no Python grammar")
                    official_smoke(executable, compiled, output/"smoke", adapter)
                for mode in config["modes"]:
                    for seed in config["seeds"]:
                        adapter.start("search", config["budget"])
                        offset = len(journal(server_output))
                        begin = time.monotonic()
                        own = None
                        if mode.startswith("restler_"):
                            strategy = {"restler_bfs": "bfs", "restler_bfs_cheap": "bfs-cheap"}[mode]
                            stop = restler_run(executable, compiled, output/"runs"/f"{variant}-{mode}-{seed}",
                                              strategy, seed, config, adapter)
                        else:
                            own = campaign(adapter, mode, "ANY", seed, config["budget"], config["depth"], config["capacity"])
                            stop = "oracle_violation" if own["detected"] else "budget"
                        events = journal(server_output)[offset:]
                        observation = characterize(events)
                        search_elapsed = time.monotonic()-begin
                        if own and (observation["calls"] != own["calls"] or observation["detected"] != own["detected"]):
                            raise AssertionError("generator and TCP observer disagree")
                        trace = revalidate(adapter, observation)
                        all_events = journal(server_output)[offset:]
                        observation["costs"] = characterize(all_events)["costs"]
                        row = {"variant": variant, "mode": mode, "seed": seed, "budget": config["budget"],
                               "depth": config["depth"], "stop": stop, "elapsed_search_s": search_elapsed,
                               **observation, "replay_trace": trace,
                               "infrastructure_errors": adapter.status()["infrastructure_errors"]}
                        rows.append(row)
                        with (output/"campaigns.jsonl").open("a") as file:
                            file.write(json.dumps(row, sort_keys=True)+"\n")
                        print(json.dumps({k: row[k] for k in ("variant", "mode", "seed", "stop", "calls", "detected", "successful_operations")}), flush=True)
            finally:
                if adapter:
                    adapter.close()
                terminate(server)
                log.close()
                events = journal(server_output)
                with gzip.open(server_output/"http.jsonl.gz", "wt") as file:
                    for event in events:
                        file.write(json.dumps(event, sort_keys=True)+"\n")
                (server_output/"http.jsonl").unlink()
    finally:
        scrub(output, tokens)
    write_json(output/"controls.json", controls)
    groups = []
    for variant in config["variants"]:
        for mode in config["modes"]:
            selected = [r for r in rows if r["variant"] == variant and r["mode"] == mode]
            groups.append({"variant": variant, "mode": mode, "campaigns": len(selected),
                           "detected": sum(r["detected"] for r in selected),
                           "calls": sum(r["calls"] for r in selected),
                           "stops": dict(Counter(r["stop"] for r in selected)),
                           "successful_operations": sorted(set().union(*(set(r["successful_operations"]) for r in selected)))})
    write_json(output/"summary.json", {"stage": config["stage"], "groups": groups, "campaigns": len(rows),
               "revalidated_witnesses": sum(bool(r["replay_trace"]) for r in rows),
               "search_calls": sum(r["calls"] for r in rows),
               "outside_domain_calls": sum(r["outside_domain"] for r in rows),
               "setup_limitations": [{"variant": r["variant"], "mode": r["mode"], "seed": r["seed"],
                                      "stop": r["stop"], "calls": r["calls"], "outside_domain": r["outside_domain"]}
                                     for r in rows if r["calls"] == 0 or r["outside_domain"] or
                                     r["infrastructure_errors"] or r["stop"] in ("wall_timeout", "tool_error", "infrastructure_error")]})
    sources = sorted(set(list((ROOT/"integrations/restler").glob("*.py"))+
                          list((ROOT/"integrations/salon").glob("*.py"))+
                          list((ROOT/"integrations/salon_ablation").glob("*.py"))+
                          list((ROOT/"backends/salon").glob("*.py"))+[config_path]))
    write_json(output/"manifest.json", {"stage": config["stage"], "config": config,
         "upstream_commit": actual, "lab_commit": os.environ.get("GITHUB_SHA"),
         "elapsed_total_s": time.time()-started, "python": sys.version,
         "sources_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
         "files_sha256": {str(p.relative_to(output)): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in sorted(output.rglob("*")) if p.is_file()}})
    if len(rows) != len(config["variants"])*len(config["modes"])*len(config["seeds"]):
        raise AssertionError("incomplete pilot; do not interpret as a completed comparison")
    if any(r["stop"] in ("infrastructure_error", "tool_error") or r["infrastructure_errors"] for r in rows):
        raise AssertionError("pilot contains infrastructure failures; preserved for investigation")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--restler", required=True)
    parser.add_argument("--upstream", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--config", default=str(ROOT/"configs/restler-pilot.json"))
    args = parser.parse_args()
    run(Path(args.restler).resolve(), Path(args.upstream).resolve(), args.out, args.config)
