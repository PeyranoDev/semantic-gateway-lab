"""FastAPI assembly; corrected by default and locally runnable."""
import hmac
from fastapi import FastAPI, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict
from .auth import issue, verify
from .db import Database, password_hash
from .service import Rejected, SalonService

class Login(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str
    password: str

class NewBooking(BaseModel):
    model_config = ConfigDict(extra="forbid")
    slot: str

def create_app(database_path, signing_key, *, variant="fixed", after_effect=None):
    if len(signing_key) < 32:
        raise ValueError("a signing key of at least 32 characters is required")
    app = FastAPI(title="TurnoSalon research backend", version="0.1.0")
    database = Database(database_path)
    service = SalonService(database, variant, after_effect)
    app.state.database, app.state.service = database, service

    def principal(authorization: str | None = Header(default=None)):
        try:
            if not authorization or not authorization.startswith("Bearer "):
                raise ValueError("missing session")
            identifier = verify(authorization[7:], signing_key)
            with database.connect() as conn:
                user = conn.execute("SELECT * FROM users WHERE id=?", (identifier,)).fetchone()
                if user is None:
                    raise ValueError("unknown principal")
                if user["role"] not in ("customer", "staff"):
                    raise HTTPException(403, "unknown role")
                return dict(user)
        except ValueError:
            raise HTTPException(401, "invalid session") from None

    def call(method, *args):
        try:
            return method(*args)
        except Rejected as exc:
            raise HTTPException(exc.status, exc.detail) from None

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/sessions")
    def login(body: Login):
        with database.connect() as conn:
            user = conn.execute("SELECT * FROM users WHERE id=?", (body.username,)).fetchone()
        candidate = password_hash(body.username, body.password)
        if user is None or not hmac.compare_digest(candidate, user["password_hash"]):
            raise HTTPException(401, "invalid credentials")
        return {"access_token": issue(user["id"], signing_key), "token_type": "bearer"}

    @app.get("/bookings")
    def list_bookings(user=Depends(principal)):
        return service.list_bookings(user)

    @app.post("/bookings", status_code=201)
    def create_booking(body: NewBooking, user=Depends(principal)):
        return call(service.create, user, body.slot)

    @app.get("/bookings/{identifier}")
    def read_booking(identifier: str, user=Depends(principal)):
        return call(service.read, user, identifier)

    def endpoint(operation):
        def handle(identifier: str, user=Depends(principal)):
            return call(service.transition, user, identifier, operation)
        return handle

    for operation in ("reserve", "pay", "confirm", "cancel", "refund"):
        app.add_api_route("/bookings/{identifier}/" + operation, endpoint(operation),
                          methods=["POST"], name=operation)
    return app
