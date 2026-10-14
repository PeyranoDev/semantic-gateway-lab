"""Disposable loopback-only HTTP/SQL observation server shared by both tools.

The wrapper does not change business handlers. Resets and budget guards belong
to the research harness, never to the production API. Native RESTler checkers
must NOT be used with sequence-header resets (some start a trace per request).
"""
import argparse
import asyncio
from dataclasses import asdict
import json
from pathlib import Path

from backends.salon.app import create_app
from backends.salon.auth import verify
from integrations.salon.model import Action, ACTORS, PUBLIC_KEY, RESOURCES
from integrations.salon.oracle import check


def normalize(method, path, authorization):
    actor = "anonymous"
    if authorization.startswith("Bearer "):
        try:
            actor = verify(authorization[7:], PUBLIC_KEY)
        except ValueError:
            pass
    if actor not in ACTORS:
        return None
    parts = path.strip("/").split("/")
    if method == "GET" and parts == ["bookings"]:
        return Action("list_bookings", actor)
    if len(parts) not in (2, 3) or parts[0] != "bookings" or parts[1] not in RESOURCES:
        return None
    if len(parts) == 2 and method == "GET":
        return Action("read_booking", actor, parts[1])
    if len(parts) == 3 and method == "POST" and parts[2] in ("reserve", "pay", "confirm", "cancel", "refund"):
        return Action(parts[2], actor, parts[1])
    return None


class Observer:
    def __init__(self, app, output):
        self.app = app
        self.database = app.state.database
        self.output = Path(output)
        self.output.mkdir(parents=True, exist_ok=True)
        self.lock = asyncio.Lock()
        self.phase = "setup"
        self.budget = 0
        self.sequence = None
        self.seen = set()
        self.episodes = 0
        self.calls = 0
        self.stopped = False
        self.events = 0
        self.errors = []
        self.journal = self.output / "http.jsonl"
        self.journal.write_text("")
        self.publish()

    def publish(self):
        status = {"phase": self.phase, "budget": self.budget, "calls": self.calls,
                  "episodes": self.episodes, "stopped": self.stopped,
                  "events": self.events, "infrastructure_errors": self.errors}
        temporary = self.output / "status.tmp"
        temporary.write_text(json.dumps(status, sort_keys=True))
        temporary.replace(self.output / "status.json")

    def record(self, event):
        self.events += 1
        event["event"] = self.events
        with self.journal.open("a") as file:
            file.write(json.dumps(event, sort_keys=True) + "\n")
        self.publish()

    @staticmethod
    async def respond(send, status, body):
        await send({"type": "http.response.start", "status": status,
                    "headers": [(b"content-type", b"application/json")]})
        await send({"type": "http.response.body", "body": json.dumps(body).encode()})

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        async with self.lock:  # One measured client; snapshots bracket exactly one HTTP call.
            method, path = scope["method"], scope["path"]
            headers = {k.decode().lower(): v.decode() for k, v in scope["headers"]}
            if path == "/_lab/start" and method == "POST":
                payload = b""
                while True:
                    message = await receive()
                    payload += message.get("body", b"")
                    if not message.get("more_body"):
                        break
                data = json.loads(payload)
                phase, budget = data["phase"], data.get("budget", 0)
                if phase not in ("validation", "search", "replay") or not isinstance(budget, int) or budget < 0:
                    return await self.respond(send, 400, {"error": "invalid phase/budget"})
                self.database.reset_fixture()
                self.phase, self.budget = phase, budget
                self.calls, self.episodes = 0, 0
                self.stopped, self.sequence, self.seen = False, None, set()
                self.record({"kind": "control", "phase": phase, "operation": "start", "budget": budget})
                return await self.respond(send, 200, {"started": True})
            if path == "/health":
                self.record({"kind": "setup", "operation": "health"})
                return await self.respond(send, 200, {"status": "ok"})
            if path == "/_lab/reset" and method == "POST":
                sequence = headers.get("x-lab-sequence")
                if not sequence or sequence in self.seen:
                    return await self.respond(send, 400, {"detail": "invalid reset sequence"})
                self.database.reset_fixture()
                self.sequence = sequence
                self.seen.add(sequence)
                self.episodes += 1
                self.record({"kind": "control", "phase": self.phase, "operation": "reset", "episode": self.episodes})
                return await self.respond(send, 200, {"reset": True})
            authentication = path == "/sessions"
            phase = "authentication" if authentication else self.phase
            if phase == "search" and (self.stopped or self.calls >= self.budget):
                self.record({"kind": "budget_gate", "phase": phase, "method": method, "path": path})
                return await self.respond(send, 503, {"detail": "research search stopped"})
            sequence = headers.get("x-restler-sequence-id") or headers.get("x-lab-sequence")
            if not authentication:
                if not sequence or (sequence != self.sequence and sequence in self.seen):
                    self.errors.append("missing_or_noncontiguous_sequence")
                    self.record({"kind": "infrastructure_error", "phase": phase, "method": method, "path": path})
                    return await self.respond(send, 400, {"detail": "invalid research sequence"})
                if sequence != self.sequence:
                    self.database.reset_fixture()
                    self.sequence = sequence
                    self.seen.add(sequence)
                    self.episodes += 1
                    self.record({"kind": "reset", "phase": phase, "episode": self.episodes})
            before = self.database.snapshot()
            captured, body = [], bytearray()

            async def capture(message):
                captured.append(message)
                if message["type"] == "http.response.body":
                    body.extend(message.get("body", b""))

            await self.app(scope, receive, capture)
            after = self.database.snapshot()
            status = next(m["status"] for m in captured if m["type"] == "http.response.start")
            try:
                result = json.loads(body)
            except ValueError:
                result = {"error": "non-json response"}
            action = normalize(method, path, headers.get("authorization", "")) if not authentication else None
            errors = check(before, action, {"status": status, "body": result}, after) if action else []
            if phase == "search":
                self.calls += 1
                self.stopped = bool(errors)
            event = {"kind": "http", "phase": phase, "method": method, "path": path,
                     "episode": self.episodes, "call": self.calls, "status": status,
                     "action": asdict(action) if action else None,
                     "domain": "normalized" if action else "authentication" if authentication else "outside",
                     "response": {"status": status, "body": {"token_omitted": True} if authentication else result},
                     "before": before, "after": after, "violations": errors}
            self.record(event)
            for message in captured:
                await send(message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", default="fixed")
    parser.add_argument("--out", required=True)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    output = Path(args.out)
    output.mkdir(parents=True, exist_ok=True)
    app = create_app(output / "salon.db", PUBLIC_KEY, variant=args.variant)
    app.state.database.provision_fixture()
    import uvicorn
    uvicorn.run(Observer(app, output), host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
