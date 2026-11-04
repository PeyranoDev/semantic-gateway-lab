"""HTTP/SQL adapter for the pinned crAPI shop (research harness).

The adapter drives the finite domain of integrations.crapi.model against the live
service, and reads and resets state through direct SQL on the disposable local
database. It is the only component that talks to crAPI; the oracle judges the
observed transitions. TLS verification is disabled because the fixture uses a
self-signed certificate bound to 127.0.0.1.
"""
import json
import ssl
import subprocess
import urllib.error
import urllib.request

from .model import ACTORS, PRICE

IDENTITY = "https://127.0.0.1:8080"
WORKSHOP = "https://127.0.0.1:8000/workshop/api/shop"
CONTEXT = ssl._create_unverified_context()
FIXTURE = {a: {"email": f"sglab-{a}@example.com", "password": f"Research-only-{a}1!"} for a in ACTORS}

def _request(method, url, body=None, token=None):
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    request = urllib.request.Request(url, method=method, data=data, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30, context=CONTEXT) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()

def _psql(*statements):
    args = ["docker", "exec", "postgresdb", "psql", "-U", "admin", "-d", "crapi", "-At", "-F", "\t"]
    for sql in statements:
        args += ["-c", sql]
    out = subprocess.run(args, capture_output=True, text=True, check=True)
    return [line.split("\t") for line in out.stdout.splitlines() if line]

class Adapter:
    """One campaign actor-set. Symbolic order targets bind to concrete ids per episode."""

    def __init__(self):
        self.tokens = {}
        self.user_id = {}
        for actor, cred in FIXTURE.items():
            status, _ = _request("POST", IDENTITY + "/identity/api/auth/signup",
                                 {"name": actor, "email": cred["email"],
                                  "number": "900000000" + str(1 + ACTORS.index(actor)),
                                  "password": cred["password"]})
            status, body = _request("POST", IDENTITY + "/identity/api/auth/login", cred)
            if status != 200:
                raise AssertionError("fixture login failed")
            self.tokens[actor] = json.loads(body)["token"]
        for row in _psql("select id,email from user_login where email like 'sglab-%'"):
            for actor, cred in FIXTURE.items():
                if cred["email"] == row[1]:
                    self.user_id[actor] = int(row[0])
        self.created = {a: [] for a in ACTORS}
        self.other_order = None
        self._cache = None
        self._seller = next(r[0] for r in _psql(
            "select id from user_login where id not in ({}) order by id limit 1".format(
                ",".join(str(i) for i in self.user_id.values()))))

    def reset(self):
        ids = ",".join(str(i) for i in self.user_id.values())
        # One docker exec: clear fixture orders, restore credit, seed one foreign order.
        _psql(f"delete from \"order\" where user_id in ({ids})",
              f"update user_details set available_credit=100 where user_id in ({ids})",
              "insert into \"order\"(user_id,product_id,quantity,status,created_on,transaction_id) "
              f"values ({self._seller},1,2,'delivered',now(),gen_random_uuid())")
        self.other_order = int(_psql(
            f"select max(id) from \"order\" where user_id={self._seller}")[0][0])
        self.created = {a: [] for a in ACTORS}
        self._cache = None

    def _order_id(self, actor, target):
        if target == "other":
            return self.other_order
        owner, index = target.split("#")
        pool = self.created[owner]
        return pool[int(index) - 1] if int(index) - 1 < len(pool) else -1

    def snapshot(self):
        if self._cache is not None:
            return json.loads(self._cache)  # unchanged since the last call: return a fresh copy
        ids = {str(i): a for a, i in self.user_id.items()}
        state = {"credit": {}, "count": {a: len(self.created[a]) for a in ACTORS},
                 "orders": {}}
        order_ids = [str(self.other_order)] + [str(i) for a in ACTORS for i in self.created[a]]
        rows = _psql("select 'c',user_id::text,available_credit::text,'' from user_details "
                     f"where user_id in ({','.join(ids)}) "
                     "union all select 'o',id::text,user_id::text,quantity||':'||status from \"order\" "
                     f"where id in ({','.join(order_ids)})")
        for tag, a, b, c in rows:
            if tag == "c":
                state["credit"][ids[a]] = round(float(b) / PRICE, 4)
            else:
                owner = ids.get(b, "other")
                key = self._symbolic(int(a), owner)
                quantity, order_status = int(c.split(":")[0]), c.split(":", 1)[1]
                paid = 2 * PRICE if key == "other" else PRICE
                # crAPI credits quantity x price on return; reconstruct it from the status.
                refunded = quantity * PRICE if order_status == "returned" else 0
                state["orders"][key] = {"owner": owner, "quantity": quantity,
                                        "status": order_status, "paid": paid, "refunded": refunded}
        self._cache = json.dumps(state, sort_keys=True)
        return state

    def _symbolic(self, order_id, owner):
        if order_id == self.other_order:
            return "other"
        return f"{owner}#{self.created[owner].index(order_id) + 1}"

    def execute(self, action):
        token = self.tokens[action.actor]
        op = action.operation
        if op not in ("read_order", "list_orders"):
            self._cache = None  # a mutating call may change state
        if op == "buy":
            status, body = _request("POST", WORKSHOP + "/orders", {"product_id": 1, "quantity": 1}, token)
            if status == 200:
                new = int(_psql(f"select max(id) from \"order\" where user_id={self.user_id[action.actor]}")[0][0])
                if new not in self.created[action.actor]:
                    self.created[action.actor].append(new)
            return {"allowed": status == 200}
        if op == "list_orders":
            status, _ = _request("GET", WORKSHOP + "/orders/all", token=token)
            return {"allowed": status == 200}
        order_id = self._order_id(action.actor, action.target)
        if op == "read_order":
            status, _ = _request("GET", f"{WORKSHOP}/orders/{order_id}", token=token)
            return {"allowed": status == 200}
        if op in ("set_returned", "set_delivered"):
            value = "returned" if op == "set_returned" else "delivered"
            status, _ = _request("PUT", f"{WORKSHOP}/orders/{order_id}",
                                 {"product_id": 1, "quantity": 1, "status": value}, token)
            return {"allowed": status == 200}
        if op == "set_quantity":
            status, _ = _request("PUT", f"{WORKSHOP}/orders/{order_id}",
                                 {"product_id": 1, "quantity": 2}, token)
            return {"allowed": status == 200}
        if op == "request_return":
            status, _ = _request("POST", f"{WORKSHOP}/orders/return_order?order_id={order_id}",
                                 {}, token)
            return {"allowed": status == 200}
        raise ValueError(op)
