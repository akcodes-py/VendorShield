"""Users + access review + audit read. WHY: least-privilege + 2-admin rule demo."""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.deps import get_current_user, require_admin, require_roles
from app.core.rate_limit import client_ip
from app.core.security import hash_password
from app.db.session import get_db
from app.models.workflow import Approval
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.auth import DecideIn, RoleRequestIn

router = APIRouter(tags=["users"])


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(default="Reviewer", pattern="^(Admin|Reviewer|Auditor|Vendor)$")
    vendor_id: int | None = None


def _out(u: User) -> dict:
    return {"id": u.id, "email": u.email, "role": u.role,
            "vendor_id": u.vendor_id, "mfa_enabled": u.mfa_enabled, "status": u.status}


# WHY: Auditor is read-only -> may list, may NOT create/revoke.
@router.get("/users")
def list_users(user: User = Depends(require_roles("Admin", "Auditor")),
               db: Session = Depends(get_db)):
    return [_out(u) for u in db.query(User).all()]


@router.post("/users", status_code=201)
def create_user(body: UserCreate, admin: User = Depends(require_admin),
                request: Request = None, db: Session = Depends(get_db)):
    if db.query(User).filter_by(email=body.email).first():
        raise HTTPException(status_code=409, detail="Email exists")
    u = User(email=body.email, password_hash=hash_password(body.password),
             role=body.role, vendor_id=body.vendor_id)
    db.add(u)
    db.flush()
    write_audit(db, admin.id, "create", "user", u.id, client_ip(request), {"email": u.email, "role": u.role})
    db.commit()
    return _out(u)


@router.get("/users/{uid}")
def get_user(uid: int, me: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # WHY: self or Admin/Auditor only; Vendor cannot see others (IDOR guard).
    if me.role not in ("Admin", "Auditor") and me.id != uid:
        raise HTTPException(status_code=403, detail="Forbidden")
    u = db.get(User, uid)
    if not u:
        raise HTTPException(status_code=404, detail="Not found")
    if me.role == "Vendor" and me.vendor_id != u.vendor_id and me.id != uid:
        raise HTTPException(status_code=403, detail="Forbidden")
    return _out(u)


@router.post("/users/{uid}/role-request", status_code=201)
def role_request(uid: int, body: RoleRequestIn, admin: User = Depends(require_admin),
                 request: Request = None, db: Session = Depends(get_db)):
    """WHY: role change needs 2nd Admin - this only creates the request."""
    target = db.get(User, uid)
    if not target:
        raise HTTPException(status_code=404, detail="Not found")
    ap = Approval(entity_type="role_change", entity_id=uid, requested_by=admin.id,
                  decision="Pending", comments=f"{target.role}->{body.new_role}: {body.reason}|new_role={body.new_role}")
    db.add(ap)
    db.flush()
    write_audit(db, admin.id, "role_request", "user", uid, client_ip(request), {"to": body.new_role})
    db.commit()
    return {"approval_id": ap.id, "status": "Pending - needs 2nd Admin"}


@router.post("/users/{uid}/revoke")
def revoke(uid: int, admin: User = Depends(require_admin),
            request: Request = None, db: Session = Depends(get_db)):
    """WHY: access-review revoke is immediate but audited."""
    u = db.get(User, uid)
    if not u:
        raise HTTPException(status_code=404, detail="Not found")
    old = u.status
    u.status = "revoked"
    write_audit(db, admin.id, "update", "user", uid, client_ip(request), {"status": [old, "revoked"]})
    db.commit()
    return _out(u)


@router.post("/users/{uid}/confirm")
def confirm_review(uid: int, admin: User = Depends(require_admin),
                   request: Request = None, db: Session = Depends(get_db)):
    """WHY: quarterly review confirm = audit proof even with no change."""
    write_audit(db, admin.id, "access_review_confirm", "user", uid, client_ip(request), {})
    db.commit()
    return {"status": "confirmed"}


@router.get("/audit-logs")
def list_audit(user: User = Depends(require_roles("Admin", "Auditor")),
               db: Session = Depends(get_db)):
    # WHY: no POST/PUT/DELETE for audit - immutable by design.
    rows = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(200).all()
    return [{"id": r.id, "actor": r.actor_id, "action": r.action,
             "entity": f"{r.entity_type}:{r.entity_id}", "ip": r.ip} for r in rows]
