"""Real ASGI HTTP requests, authenticated sessions and independently queried SQL."""
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Lock
from fastapi.testclient import TestClient
from backends.salon.app import create_app
from .model import ACTORS, PUBLIC_KEY

class Adapter:
    def __init__(self, variant="fixed", after_effect=None):
        self.directory = TemporaryDirectory(prefix="sglab-salon-")
        self.app = create_app(Path(self.directory.name) / "salon.db", PUBLIC_KEY,
                              variant=variant, after_effect=after_effect)
        self.database = self.app.state.database
        self.database.provision_fixture()
        self.http_calls = 0
        self._lock = Lock()
        @self.app.middleware("http")
        async def count(request, call_next):
            with self._lock:
                self.http_calls += 1
            return await call_next(request)
        self.client = TestClient(self.app, raise_server_exceptions=False)
        self.client.__enter__()
        self.headers = {"anonymous": {}}
        for actor in ACTORS:
            if actor == "anonymous":
                continue
            response = self.client.post("/sessions", json={"username": actor,
                                        "password": "research-only-" + actor})
            if response.status_code != 200:
                raise AssertionError("fixture login failed")
            self.headers[actor] = {"Authorization": "Bearer " + response.json()["access_token"]}
        self.authentication_calls = self.http_calls

    def reset(self):
        self.database.reset_fixture()

    def snapshot(self):
        return self.database.snapshot()

    def execute(self, action):
        if action.operation == "list_bookings":
            response = self.client.get("/bookings", headers=self.headers[action.actor])
        elif action.operation == "read_booking":
            response = self.client.get("/bookings/" + action.resource, headers=self.headers[action.actor])
        else:
            response = self.client.post("/bookings/" + action.resource + "/" + action.operation,
                                        headers=self.headers[action.actor])
        try:
            body = response.json()
        except ValueError:
            body = {"error": "non-json response"}
        return {"status": response.status_code, "body": body}

    def close(self):
        self.client.__exit__(None, None, None)
        self.directory.cleanup()
