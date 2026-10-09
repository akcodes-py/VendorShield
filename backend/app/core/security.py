"""Password + JWT + TOTP. WHY: all crypto in one place, easy to audit."""
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
import pyotp

from app.core.config import settings


# --- Passwords: bcrypt. WHY: slow hash blocks brute-force vs SHA256. ---
def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


# --- JWT: short access + long refresh. WHY: stolen access dies in 15 min. ---
def _encode(payload: dict) -> str:
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_access(user_id: int, role: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_MINUTES)
    return _encode({"sub": str(user_id), "role": role, "type": "access", "exp": exp})


def create_refresh(user_id: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_DAYS)
    # WHY: jti lets us revoke one refresh without killing all sessions.
    return _encode({"sub": str(user_id), "type": "refresh", "jti": str(uuid.uuid4()), "exp": exp})


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


# --- TOTP MFA: pyotp. WHY: no SMS cost, works offline, standard for Admin. ---
def new_mfa_secret() -> str:
    return pyotp.random_base32()


def mfa_uri(secret: str, email: str) -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name="VendorShield")


def verify_totp(secret: str, code: str) -> bool:
    try:
        return pyotp.TOTP(secret).verify(code, valid_window=1)
    except Exception:
        return False
