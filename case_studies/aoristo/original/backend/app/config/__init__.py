"""Fixture-only settings; no production credentials or external integrations."""
import os
from types import SimpleNamespace
settings=SimpleNamespace(
    resolved_database_url=os.environ.get("DATABASE_URL", "postgresql://lab:lab@127.0.0.1/sglab_case"),
    secret_key=os.environ.get("SECRET_KEY", "semantic-gateway-lab-test-only-key-2026"),
    jwt_algorithm="HS256", jwt_issuer="AoristoTech", jwt_audience="AoristoTechApps",
    access_token_expire_minutes=43200, debug=False,
)
