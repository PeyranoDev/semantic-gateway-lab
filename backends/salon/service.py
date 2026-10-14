"""Business rules and SQL effects; no imports from the experimental harness."""
from uuid import uuid4

VARIANTS = ("fixed", "read_scope", "slot_capacity", "confirm_unpaid", "refund_replay")

class Rejected(Exception):
    def __init__(self, status, detail):
        self.status, self.detail = status, detail

def scoped(user, booking):
    return user["role"] in ("customer", "staff") and user["tenant"] == booking["tenant"] and (
        user["role"] == "staff" or user["id"] == booking["customer"])

def public(row):
    return {k: row[k] for k in ("id", "tenant", "customer", "slot", "status", "paid", "refunded")}

class SalonService:
    def __init__(self, database, variant="fixed", after_effect=None):
        if variant not in VARIANTS:
            raise ValueError("unknown research variant")
        self.database, self.variant, self.after_effect = database, variant, after_effect

    def list_bookings(self, user):
        with self.database.connect() as conn:
            return [public(row) for row in conn.execute("SELECT * FROM bookings ORDER BY id")
                    if scoped(user, row)]

    def read(self, user, identifier):
        with self.database.connect() as conn:
            row = conn.execute("SELECT * FROM bookings WHERE id=?", (identifier,)).fetchone()
            if row is None or (self.variant != "read_scope" and not scoped(user, row)):
                raise Rejected(404, "booking not found")
            return public(row)

    def create(self, user, slot_id):
        if user["role"] != "customer":
            raise Rejected(403, "customer required")
        with self.database.transaction() as conn:
            slot = conn.execute("SELECT * FROM slots WHERE id=? AND tenant=?",
                                (slot_id, user["tenant"])).fetchone()
            if slot is None:
                raise Rejected(404, "slot not found")
            identifier = str(uuid4())
            conn.execute("INSERT INTO bookings VALUES (?,?,?,?,?,0,0)",
                         (identifier, user["tenant"], user["id"], slot_id, "draft"))
            return public(conn.execute("SELECT * FROM bookings WHERE id=?", (identifier,)).fetchone())

    def transition(self, user, identifier, operation):
        with self.database.transaction() as conn:
            booking = conn.execute("SELECT * FROM bookings WHERE id=?", (identifier,)).fetchone()
            if booking is None or not scoped(user, booking):
                raise Rejected(404, "booking not found")
            slot = conn.execute("SELECT * FROM slots WHERE id=?", (booking["slot"],)).fetchone()
            if operation in ("confirm", "refund") and user["role"] != "staff":
                raise Rejected(403, "staff required")
            if operation == "reserve":
                if booking["status"] != "draft":
                    raise Rejected(409, "booking is not draft")
                if self.variant != "slot_capacity" and slot["occupied"] >= slot["capacity"]:
                    raise Rejected(409, "slot full")
                conn.execute("UPDATE slots SET occupied=occupied+1 WHERE id=?", (slot["id"],))
                conn.execute("UPDATE bookings SET status='reserved' WHERE id=?", (identifier,))
            elif operation == "pay":
                if user["role"] != "customer" or user["id"] != booking["customer"]:
                    raise Rejected(403, "booking customer required")
                if booking["status"] != "reserved" or booking["paid"]:
                    raise Rejected(409, "booking cannot be paid")
                customer = conn.execute("SELECT * FROM users WHERE id=?", (user["id"],)).fetchone()
                if customer["balance"] < slot["price"]:
                    raise Rejected(409, "insufficient credit")
                conn.execute("UPDATE users SET balance=balance-? WHERE id=?", (slot["price"], user["id"]))
                conn.execute("UPDATE bookings SET paid=? WHERE id=?", (slot["price"], identifier))
                conn.execute("INSERT INTO ledger(booking,customer,kind,amount) VALUES (?,?,?,?)",
                             (identifier, user["id"], "payment", slot["price"]))
            elif operation == "confirm":
                if booking["status"] != "reserved" or (
                    self.variant != "confirm_unpaid" and booking["paid"] != slot["price"]):
                    raise Rejected(409, "paid reservation required")
                conn.execute("UPDATE bookings SET status='confirmed' WHERE id=?", (identifier,))
            elif operation == "cancel":
                if booking["status"] not in ("reserved", "confirmed"):
                    raise Rejected(409, "booking cannot be cancelled")
                conn.execute("UPDATE slots SET occupied=occupied-1 WHERE id=?", (slot["id"],))
                conn.execute("UPDATE bookings SET status='cancelled' WHERE id=?", (identifier,))
            elif operation == "refund":
                if booking["status"] != "cancelled" or not booking["paid"] or (
                    self.variant != "refund_replay" and booking["refunded"]):
                    raise Rejected(409, "booking cannot be refunded")
                conn.execute("UPDATE users SET balance=balance+? WHERE id=?",
                             (booking["paid"], booking["customer"]))
                conn.execute("UPDATE bookings SET refunded=paid WHERE id=?", (identifier,))
                conn.execute("INSERT INTO ledger(booking,customer,kind,amount) VALUES (?,?,?,?)",
                             (identifier, booking["customer"], "refund", booking["paid"]))
            else:
                raise ValueError("unknown transition")
            if self.after_effect is not None:
                self.after_effect(operation)  # Rollback tests inject failures only here.
            return public(conn.execute("SELECT * FROM bookings WHERE id=?", (identifier,)).fetchone())
