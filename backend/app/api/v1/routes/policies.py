"""Policy library. WHY: version history proves what was approved when."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.deps import require_roles
from app.core.rate_limit import client_ip
from app.db.session import get_db
from app.models.policy import Policy, PolicyVersion
from app.models.user import User
from app.schemas.governance import PolicyCreate, PolicyUpdate, VersionCreate

router = APIRouter(tags=["policies"])
VIEW = require_roles("Admin", "Reviewer", "Auditor")
EDIT = require_roles("Admin", "Reviewer")


def _out(p: Policy) -> dict:
    return {"id": p.id, "title": p.title, "version": p.version, "owner": p.owner,
            "approval_status": p.approval_status,
            "review_date": str(p.review_date) if p.review_date else None,
            "is_sample": bool(p.is_sample)}


@router.get("/policies")
def list_policies(user: User = Depends(VIEW), db: Session = Depends(get_db)):
    return [_out(p) for p in db.query(Policy).all()]


@router.post("/policies", status_code=201)
def create_policy(body: PolicyCreate, user: User = Depends(EDIT),
                  request: Request = None, db: Session = Depends(get_db)):
    p = Policy(title=body.title, version="1.0", owner=body.owner or user.email,
               approval_status="Draft", review_date=body.review_date, is_sample=0)
    db.add(p)
    db.flush()
    # WHY: v1.0 snapshot at creation - history starts day one.
    db.add(PolicyVersion(policy_id=p.id, version="1.0", content=body.content or "(empty SAMPLE)"))
    write_audit(db, user.id, "create", "policy", p.id, client_ip(request), {"title": p.title})
    db.commit()
    return _out(p)


@router.get("/policies/{pid}")
def get_policy(pid: int, user: User = Depends(VIEW), db: Session = Depends(get_db)):
    p = db.get(Policy, pid)
    if not p:
        raise HTTPException(status_code=404, detail="Not found")
    return _out(p)


@router.patch("/policies/{pid}")
def update_policy(pid: int, body: PolicyUpdate, user: User = Depends(EDIT),
                  request: Request = None, db: Session = Depends(get_db)):
    p = db.get(Policy, pid)
    if not p:
        raise HTTPException(status_code=404, detail="Not found")
    old = p.approval_status
    # WHY: only Admin approves; Reviewer may only move to Pending.
    if body.approval_status == "Approved" and user.role != "Admin":
        raise HTTPException(status_code=403, detail="Only Admin can Approve")
    p.approval_status = body.approval_status
    if body.review_date is not None:
        p.review_date = body.review_date
    write_audit(db, user.id, "update", "policy", pid, client_ip(request), {"approval": [old, p.approval_status]})
    db.commit()
    return _out(p)


@router.get("/policies/{pid}/versions")
def list_versions(pid: int, user: User = Depends(VIEW), db: Session = Depends(get_db)):
    if not db.get(Policy, pid):
        raise HTTPException(status_code=404, detail="Not found")
    return [{"id": v.id, "version": v.version, "content": v.content[:500]}
            for v in db.query(PolicyVersion).filter_by(policy_id=pid).order_by(PolicyVersion.id).all()]


@router.post("/policies/{pid}/versions", status_code=201)
def add_version(pid: int, body: VersionCreate, user: User = Depends(EDIT),
                request: Request = None, db: Session = Depends(get_db)):
    p = db.get(Policy, pid)
    if not p:
        raise HTTPException(status_code=404, detail="Not found")
    if db.query(PolicyVersion).filter_by(policy_id=pid, version=body.version).first():
        raise HTTPException(status_code=409, detail="Version exists")
    v = PolicyVersion(policy_id=pid, version=body.version, content=body.content)
    db.add(v)
    p.version = body.version  # WHY: policy row always shows latest
    write_audit(db, user.id, "update", "policy", pid, client_ip(request), {"new_version": body.version})
    db.commit()
    return {"id": v.id, "version": v.version}
