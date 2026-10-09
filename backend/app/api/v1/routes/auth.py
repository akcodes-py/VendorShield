"""Login + refresh + MFA. WHY: brute-force + MFA checks live here, not in routes."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.rate_limit import (
    check_login_allowed, clear_failed_login, client_ip,
    is_revoked, record_failed_login, revoke_refresh,
)
from app.core.security import (
    create_access, create_refresh, decode_token,
    new_mfa_secret, mfa_uri, verify_password, verify_totp,
)
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginIn, MFASetupOut, MFAVerifyIn, RefreshIn, TokenOut
from app.services.detection import log_event

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, request: Request, db: Session = Depends(get_db)):
    ip = client_ip(request)
    check_login_allowed(ip)  # WHY: 429 before DB hit on flood.
    user = db.query(User).filter_by(email=body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        record_failed_login(ip)
        # WHY: SOC fact for brute-force rule (5 in 5 min).
        log_event(db, "failed_login", user.id if user else None, ip, f"email={body.email}")
        write_audit(db, user.id if user else None, "login_failed",
                    "user", user.id if user else None, ip, {"email": body.email})
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if user.status != "active":
        raise HTTPException(status_code=401, detail="User revoked")

    # WHY: Admin must use TOTP once enabled; first login forces setup.
    mfa_needed = False
    if user.role == "Admin":
        if user.mfa_enabled:
            if not body.totp_code or not verify_totp(user.mfa_secret or "", body.totp_code):
                record_failed_login(ip)
                raise HTTPException(status_code=401, detail="Admin MFA code required/invalid")
        else:
            mfa_needed = True  # warn client to call /mfa/setup

    clear_failed_login(ip)
    # WHY: success facts enable new-IP rule.
    log_event(db, "login_success", user.id, ip, f"email={user.email}")
    write_audit(db, user.id, "login", "user", user.id, ip, {})
    db.commit()
    return TokenOut(access_token=create_access(user.id, user.role),
                    refresh_token=create_refresh(user.id),
                    mfa_required=mfa_needed)


@router.post("/refresh", response_model=TokenOut)
def refresh(body: RefreshIn, request: Request, db: Session = Depends(get_db)):
    try:
        data = decode_token(body.refresh_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    if data.get("type") != "refresh" or is_revoked(data.get("jti", "")):
        raise HTTPException(status_code=401, detail="Refresh revoked, login again")
    # WHY: rotation - old jti dies now, new pair issued.
    revoke_refresh(data["jti"])
    user = db.get(User, int(data["sub"]))
    if not user or user.status != "active":
        raise HTTPException(status_code=401, detail="User revoked")
    write_audit(db, user.id, "refresh", "user", user.id, client_ip(request), {})
    db.commit()
    return TokenOut(access_token=create_access(user.id, user.role),
                    refresh_token=create_refresh(user.id))


@router.post("/mfa/setup", response_model=MFASetupOut)
def mfa_setup(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # WHY: store secret now, enable only after verify proves device works.
    if not user.mfa_secret:
        user.mfa_secret = new_mfa_secret()
        db.commit()
        db.refresh(user)
    return MFASetupOut(secret=user.mfa_secret or "", otpauth_url=mfa_uri(user.mfa_secret or "", user.email))


@router.post("/mfa/verify")
def mfa_verify(body: MFAVerifyIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user.mfa_secret or not verify_totp(user.mfa_secret, body.code):
        raise HTTPException(status_code=400, detail="Invalid MFA code")
    user.mfa_enabled = True
    write_audit(db, user.id, "mfa_enabled", "user", user.id, "", {})
    db.commit()
    return {"status": "mfa_enabled"}
