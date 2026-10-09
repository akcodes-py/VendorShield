"""In-memory rate limit. WHY: blocks brute-force login without Redis (local dev)."""
import time
from collections import defaultdict

from fastapi import HTTPException, Request

# ip -> [timestamps of failed attempts]
_failed: dict[str, list[float]] = defaultdict(list)
# revoked refresh jti set. WHY: rotation - old refresh dies after use.
_revoked_refresh: set[str] = set()

WINDOW_SEC = 5 * 60
MAX_FAILS = 5


def _prune(ip: str):
    now = time.time()
    _failed[ip] = [t for t in _failed[ip] if now - t < WINDOW_SEC]


def check_login_allowed(ip: str):
    _prune(ip)
    if len(_failed[ip]) >= MAX_FAILS:
        # WHY: 429 not 403 - tells client to slow down, logged as SOC event later.
        raise HTTPException(status_code=429, detail="Too many login attempts. Try after 5 minutes.")


def record_failed_login(ip: str):
    _failed[ip].append(time.time())


def clear_failed_login(ip: str):
    _failed.pop(ip, None)


def revoke_refresh(jti: str):
    _revoked_refresh.add(jti)


def is_revoked(jti: str) -> bool:
    return jti in _revoked_refresh


def client_ip(request: Request) -> str:
    # WHY: X-Forwarded-For first only if you trust proxy; locally use client.host.
    return request.client.host if request.client else "unknown"


def reset_for_tests():
    _failed.clear()
    _revoked_refresh.clear()
