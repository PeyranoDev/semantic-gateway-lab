"""Signed expiring sessions; identity attributes are resolved from SQL."""
import base64
import hashlib
import hmac
import json
import time

def _encode(value):
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()

def issue(user, key, now=None):
    payload = _encode(json.dumps({"sub": user, "exp": int(now if now is not None else time.time()) + 3600},
                                 sort_keys=True, separators=(",", ":")).encode())
    signature = _encode(hmac.new(key.encode(), payload.encode(), hashlib.sha256).digest())
    return payload + "." + signature

def verify(token, key, now=None):
    try:
        payload, signature = token.split(".")
        expected = _encode(hmac.new(key.encode(), payload.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise ValueError("invalid session")
        obj = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        current = now if now is not None else time.time()
        if not isinstance(obj["sub"], str) or not isinstance(obj["exp"], int) or obj["exp"] <= current:
            raise ValueError("invalid session")
        return obj["sub"]
    except (ValueError, KeyError, TypeError) as exc:
        raise ValueError("invalid session") from exc
