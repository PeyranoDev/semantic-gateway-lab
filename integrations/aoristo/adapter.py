"""Original FastAPI ASGI HTTP pipeline + original SQLAlchemy repositories.

Only get_db is overridden, to isolate each serial program in a rollback transaction.
Authorization dependencies, schemas and use cases are not replaced or patched.
"""
import hashlib
import json
import logging
import os
from pathlib import Path
import sys

from .model import SOURCE_COMMIT, PUBLIC_KEY, uid

def source_manifest(source):
    root = Path(source).resolve()
    files = sorted((root / "backend/app").rglob("*.py"))
    if not files or not (root / "backend/app/main.py").is_file():
        raise ValueError("source must contain the pinned AoristoTech backend/app")
    hashes = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    combined = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
    return {"repository": "PeyranoDev/AoristoTech", "expected_commit": SOURCE_COMMIT,
            "app_files": hashes, "app_sha256": combined}

def validate_database_url(url):
    from urllib.parse import urlsplit
    parsed = urlsplit(url)
    if (parsed.scheme not in ("postgresql", "postgresql+psycopg2")
            or parsed.hostname not in ("127.0.0.1", "localhost")
            or not parsed.path.startswith("/sglab_") or parsed.query or parsed.fragment):
        raise ValueError("requires loopback PostgreSQL and a dedicated database named sglab_*")

class Adapter:
    def __init__(self, source, database_url):
        validate_database_url(database_url)
        self.manifest = source_manifest(source)
        lock = json.loads(Path(__file__).with_name("source-lock.json").read_text())
        if self.manifest != lock:
            raise ValueError("AoristoTech app differs from the pinned source lock")
        self.database_url = database_url
        # Configure before importing the original application. Ignore inherited live settings.
        if any(name == "app" or name.startswith("app.") for name in sys.modules):
            raise RuntimeError("AoristoTech must be imported in a fresh interpreter")
        for name in ("DATABASE_URL_PRODUCTION", "DATABASE_URL_STAGING", "MERCADOPAGO_ACCESS_TOKEN",
                     "MERCADOPAGO_CLIENT_SECRET", "EMAIL_API_TOKEN", "VAPID_PRIVATE_KEY"):
            os.environ[name] = ""
        os.environ.update(DATABASE_URL=database_url, APP_ENV="development", SECRET_KEY=PUBLIC_KEY,
                          DEBUG="false", EMAILS_ENABLED="false", CORS_ORIGINS="http://testserver")
        sys.path.insert(0, str(Path(source).resolve() / "backend"))
        # Source .env files are never loaded: run from a temporary empty cwd.
        import tempfile
        previous = Path.cwd()
        with tempfile.TemporaryDirectory(prefix="sglab-import-") as folder:
            os.chdir(folder)
            try:
                from app.main import app
                from app.infrastructure.database import Base, get_db
            finally:
                os.chdir(previous)
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from fastapi.testclient import TestClient
        from app.infrastructure.api.dependencies.auth import create_access_token
        from app.domain.models.user import User
        from app.domain.models.profiles import VerdusoftProfile, RedVecinaProfile
        from app.domain.models.grocery import Grocery
        from app.domain.models.product import Product
        from app.domain.models.category import Category
        from app.domain.models.inventory import InventoryItem
        from app.domain.models.sale import Sale, SaleItem
        from app.domain.models.redvecina import Building, Unit, Invitation
        self.models = dict(User=User, VerdusoftProfile=VerdusoftProfile, RedVecinaProfile=RedVecinaProfile,
                           Grocery=Grocery, Product=Product, Category=Category, Inventory=InventoryItem,
                           Sale=Sale, SaleItem=SaleItem, Building=Building, Unit=Unit, Invitation=Invitation)
        self.engine = create_engine(database_url)
        # Dedicated disposable DB only. Fail rather than deleting existing tables.
        from sqlalchemy import inspect
        if inspect(self.engine).get_table_names():
            raise ValueError("database must be empty; refusing to reuse existing tables")
        Base.metadata.create_all(self.engine)
        self.connection = self.engine.connect()
        self.Session = sessionmaker(bind=self.connection, join_transaction_mode="create_savepoint")
        self.transaction = None
        self.app, self.get_db = app, get_db
        def get_test_db():
            session = self.Session()
            try:
                yield session
            finally:
                session.close()
        app.dependency_overrides[get_db] = get_test_db
        self.tokens = {name: create_access_token({"sub": str(uid(i)), "role": 2})
                       for name, i in (("alice", 101), ("bob", 102), ("ruth", 103), ("nina", 104))}
        self.client_context = TestClient(app, raise_server_exceptions=False)
        self.client = self.client_context.__enter__()
        # The source emits identity/debug lines per call. Results keep named actors only.
        logging.getLogger("app.infrastructure.api.dependencies.auth").setLevel(logging.CRITICAL)
        logging.getLogger("app.infrastructure.api.dependencies.service_guards").setLevel(logging.CRITICAL)
        self.reset()

    def reset(self):
        from datetime import datetime, timedelta
        from sqlalchemy import text
        if self.transaction is not None:
            self.transaction.rollback()
        self.transaction = self.connection.begin()
        m = self.models
        session = self.Session()
        try:
            session.add_all([m["Grocery"](Id=i, Name=f"Fixture grocery {i}") for i in (1, 2)])
            session.add_all([m["Building"](Id=uid(200+i), Name=f"Fixture building {i}") for i in (1, 2)])
            session.flush()
            session.add_all([m["Unit"](Id=uid(300+i), BuildingId=uid(200+i), UnitNumber=str(i)) for i in (1, 2)])
            session.add_all([m["User"](Id=uid(100+i), Name=name, Email=f"{name}@example.invalid",
                                      PasswordHash="fixture-not-a-login-password", IsActive=True)
                             for i, name in enumerate(("alice", "bob", "ruth", "nina"), 1)])
            session.add(m["Product"](Id=1, Name="Fixture product"))
            session.flush()
            for i in (1, 2):
                session.add(m["VerdusoftProfile"](Id=uid(400+i), UserId=uid(100+i), GroceryId=i, Role=2))
                session.add(m["RedVecinaProfile"](Id=uid(500+i), UserId=uid(102+i),
                                                  BuildingId=uid(200+i), UnitId=uid(300+i), Role="resident"))
                session.add(m["Category"](Id=i, Name=f"Fixture category {i}", GroceryId=i))
            session.flush()
            for i in (1, 2):
                session.add(m["Inventory"](Id=i, ProductId=1, GroceryId=i, CategoryId=i,
                                            Stock=7, SalePrice=2, Unit="u"))
                session.add(m["Sale"](Id=i, UserId=uid(100+i), GroceryId=i, Total=6, Subtotal=6,
                                     Status="pending", Items=[m["SaleItem"](ProductId=1,
                                     ProductName="Fixture product", Quantity=3, UnitPrice=2, Subtotal=6)]))
                session.add(m["Invitation"](Id=uid(600+i), UnitId=uid(300+i),
                                             Token=f"public-fixture-capability-{i}", CurrentUses=0,
                                             MaxUses=1, ExpiresAt=datetime.utcnow()+timedelta(days=1)))
            session.flush()
            # SERIAL values are not rolled back; explicit fixtures don't advance them.
            session.commit()
        finally:
            session.close()

    def snapshot(self):
        m = self.models
        session = self.Session()
        try:
            sales = {"a" if v.Id == 1 else "b": {"grocery": v.GroceryId, "status": v.Status,
                      "quantity": int(sum(i.Quantity for i in v.Items))}
                     for v in session.query(m["Sale"]).order_by(m["Sale"].Id)}
            inventory = {str(v.GroceryId): v.Stock for v in session.query(m["Inventory"])}
            invitations = {}
            for v in session.query(m["Invitation"]).order_by(m["Invitation"].CreatedAt, m["Invitation"].Id):
                key = {uid(601): "a", uid(602): "b"}.get(v.Id)
                if key is None:
                    key = f"new-{len([k for k in invitations if k.startswith('new-')])+1}"
                invitations[key] = {"unit": {uid(301): "a", uid(302): "b"}.get(v.UnitId, "other"),
                                     "uses": v.CurrentUses, "max_uses": v.MaxUses}
            return {"sales": sales, "inventory": inventory, "invitations": invitations}
        finally:
            session.close()

    def execute(self, action):
        resource = {"a": 1, "b": 2, "missing": 999}[action.resource]
        headers = {} if action.actor == "anonymous" else {"Authorization": "Bearer "+self.tokens[action.actor]}
        op = action.operation
        if op == "list_sales":
            response = self.client.get("/api/Sales", headers=headers)
        elif op == "read_sale":
            response = self.client.get(f"/api/Sales/{resource}", headers=headers)
        elif op == "cancel_sale":
            response = self.client.post(f"/api/Sales/{resource}/cancel", headers=headers)
        elif op == "create_invitation":
            response = self.client.post("/api/RedVecina/Invitations", headers=headers,
                json={"UnitId": str(uid(300+resource)), "MaxUses": 1, "ValidDays": 1})
        elif op == "list_invitations":
            response = self.client.get("/api/RedVecina/Invitations", headers=headers,
                params={"unit_id": str(uid(300+resource))})
        elif op == "revoke_invitation":
            response = self.client.delete(f"/api/RedVecina/Invitations/{uid(600+resource)}", headers=headers)
        elif op == "consume_invitation":
            response = self.client.post("/api/RedVecina/Invitations/validate", headers=headers,
                json={"Token": f"public-fixture-capability-{resource}"})
        else:
            raise ValueError("unknown operation")
        try:
            body = response.json()
        except ValueError:
            body = {"error": response.text[:200]}
        # Generated UUIDs/tokens/timestamps do not belong in published semantic traces.
        def clean(value):
            if isinstance(value, dict):
                return {key: clean(v) for key, v in value.items()
                        if key not in ("Token", "token", "CreatedAt", "ExpiresAt", "Date", "date")}
            if isinstance(value, list):
                return [clean(v) for v in value]
            return value
        return {"status": response.status_code, "body": clean(body)}

    def close(self):
        self.client_context.__exit__(None, None, None)
        self.app.dependency_overrides.pop(self.get_db, None)
        if self.transaction is not None:
            self.transaction.rollback()
        self.connection.close()
        self.engine.dispose()
