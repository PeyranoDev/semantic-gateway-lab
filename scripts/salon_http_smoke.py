"""Launch the corrected backend and complete a business workflow over loopback TCP."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

KEY = "salon-research-public-fixture-signing-key-only"
BASE = "http://127.0.0.1:8765"

def request(path, body=None, token=None):
    headers = {"Content-Type":"application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = Request(BASE + path, data=json.dumps(body).encode() if body is not None else None,
                  headers=headers)
    with urlopen(req, timeout=10) as response:
        return response.status, json.load(response)

def main():
    with tempfile.TemporaryDirectory(prefix="salon-tcp-") as directory:
        env = {**os.environ, "SALON_SIGNING_KEY":KEY}
        process = subprocess.Popen([sys.executable,"-m","backends.salon","--db",
                                    str(Path(directory)/"demo.db"),"--fixture","--port","8765"],
                                   env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            for _ in range(100):
                if process.poll() is not None:
                    raise AssertionError("backend exited before readiness")
                try:
                    assert request("/health")[0] == 200
                    break
                except URLError:
                    time.sleep(.1)
            else:
                raise AssertionError("backend did not start")
            tokens = {}
            for actor in ("alice","staff_a"):
                status, body = request("/sessions", {"username":actor, "password":"research-only-"+actor})
                assert status == 200
                tokens[actor] = body["access_token"]
            status, body = request("/bookings", {"slot":"a"}, tokens["alice"])
            assert status == 201 and body["customer"] == "alice"
            identifier = body["id"]
            statuses = []
            for op, actor in (("reserve","alice"),("pay","alice"),("confirm","staff_a"),
                              ("cancel","alice"),("refund","staff_a")):
                status, body = request("/bookings/"+identifier+"/"+op, {}, tokens[actor])
                assert status == 200
                statuses.append(status)
            status, body = request("/bookings/"+identifier, token=tokens["alice"])
            assert status == 200 and body["status"] == "cancelled" and body["paid"] == body["refunded"] == 1000
            print(json.dumps({"transport":"loopback TCP","workflow_statuses":statuses,"passed":True}))
        finally:
            process.terminate()
            process.wait(timeout=10)

if __name__ == "__main__":
    main()
