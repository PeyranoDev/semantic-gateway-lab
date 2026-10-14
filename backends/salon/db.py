"""SQLite persistence with committed business transactions."""
from contextlib import contextmanager
import hashlib
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
 id TEXT PRIMARY KEY, tenant TEXT NOT NULL, role TEXT NOT NULL,
 password_hash TEXT NOT NULL, balance INTEGER NOT NULL CHECK(balance >= 0)
);
CREATE TABLE IF NOT EXISTS slots (
 id TEXT PRIMARY KEY, tenant TEXT NOT NULL, service TEXT NOT NULL,
 price INTEGER NOT NULL CHECK(price > 0), capacity INTEGER NOT NULL CHECK(capacity > 0),
 occupied INTEGER NOT NULL DEFAULT 0 CHECK(occupied >= 0)
);
CREATE TABLE IF NOT EXISTS bookings (
 id TEXT PRIMARY KEY, tenant TEXT NOT NULL, customer TEXT NOT NULL REFERENCES users(id),
 slot TEXT NOT NULL REFERENCES slots(id), status TEXT NOT NULL,
 paid INTEGER NOT NULL DEFAULT 0, refunded INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS ledger (
 id INTEGER PRIMARY KEY, booking TEXT NOT NULL REFERENCES bookings(id),
 customer TEXT NOT NULL REFERENCES users(id), kind TEXT NOT NULL, amount INTEGER NOT NULL
);
"""

def password_hash(user, password):
    # Deterministic salts belong to synthetic fixtures only; no registration API.
    return hashlib.pbkdf2_hmac("sha256", password.encode(),
                               ("salon-fixture-" + user).encode(), 100_000).hex()

class Database:
    def __init__(self, path):
        self.path = str(path)
        with self.connect() as conn:
            conn.executescript(SCHEMA)
            conn.execute("PRAGMA journal_mode=WAL")

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.path, timeout=20, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def transaction(self):
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                yield conn
                conn.commit()
            except BaseException:
                conn.rollback()
                raise

    def provision_fixture(self):
        """Only call on a disposable research database."""
        self._credentials = {u: password_hash(u, "research-only-" + u)
                             for u in ("alice", "bob", "staff_a", "staff_b")}
        self.reset_fixture()

    def reset_fixture(self):
        with self.transaction() as conn:
            for table in ("ledger", "bookings", "slots", "users"):
                conn.execute("DELETE FROM " + table)
            for user, tenant, role in (("alice", "a", "customer"), ("bob", "b", "customer"),
                                       ("staff_a", "a", "staff"), ("staff_b", "b", "staff")):
                conn.execute("INSERT INTO users VALUES (?,?,?,?,?)",
                             (user, tenant, role, self._credentials[user],
                              5000 if role == "customer" else 0))
            for slot, price in (("a", 1000), ("b", 1500)):
                conn.execute("INSERT INTO slots VALUES (?,?,?,?,?,?)",
                             (slot, slot, "haircut", price, 1, 0))
            for identifier, tenant, owner in (("a", "a", "alice"), ("a2", "a", "alice"),
                                               ("b", "b", "bob"), ("b2", "b", "bob")):
                conn.execute("INSERT INTO bookings VALUES (?,?,?,?,?,0,0)",
                             (identifier, tenant, owner, tenant, "draft"))

    def snapshot(self):
        with self.connect() as conn:
            return {
                "users": {r["id"]: {k: r[k] for k in ("tenant", "role", "balance")}
                          for r in conn.execute("SELECT * FROM users ORDER BY id")},
                "slots": {r["id"]: {k: r[k] for k in
                          ("tenant", "service", "price", "capacity", "occupied")}
                          for r in conn.execute("SELECT * FROM slots ORDER BY id")},
                "bookings": {r["id"]: {k: r[k] for k in
                             ("tenant", "customer", "slot", "status", "paid", "refunded")}
                             for r in conn.execute("SELECT * FROM bookings ORDER BY id")},
                "ledger": [dict(r) for r in conn.execute(
                    "SELECT booking,customer,kind,amount FROM ledger ORDER BY id")],
            }
