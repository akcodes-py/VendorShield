"""Auth dependencies. WHY: RBAC enforced here, routes stay thin."""
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User

_bearer = HTTPBearer(auto_error=True)

# Role hierarchy for interview: Admin > Reviewer > Auditor(read-only) > Vendor(scoped).
READ_ONLY_ROLES = {"Auditor"}


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    try:
        data = decode_token(creds.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if data.get("type") != "access":
        raise HTTPException(status_code=401, detail="Access token required")
    user = db.get(User, int(data["sub"]))
    if not user or user.status != "active":
        raise HTTPException(status_code=401, detail="User revoked or missing")
    return user


def require_roles(*allowed: str):
    """WHY: least privilege - each endpoint declares who may call it."""
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            # WHY: 403 logged as perm_denied SOC event in later phases.
            raise HTTPException(status_code=403, detail=f"Requires role {allowed}")
        return user
    return checker


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "Admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return user
