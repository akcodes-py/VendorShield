"""Continuity per vendor + gaps report. WHY: critical vendors must prove exit plan."""
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.deps import get_current_user, require_roles
from app.core.rate_limit import client_ip
from app.db.session import get_db
from app.models.continuity import Continuity
from app.models.user import User
from app.models.vendor import Vendor
from app.schemas.governance import ContinuityUpdate

router = APIRouter(tags=["continuity"])
VIEW = require_roles("Admin", "Reviewer", "Auditor")


def _out(vendor: Vendor, c: Continuity | None) -> dict:
    return {"vendor_id": vendor.id, "name": vendor.name, "tier": vendor.tier,
            "data_access": vendor.data_access,
            "rto_hours": c.rto_hours if c else None, "rpo_hours": c.rpo_hours if c else None,
            "plan_available": bool(c.plan_available) if c else False,
            "last_test_date": str(c.last_test_date) if c and c.last_test_date else None,
            "exit_plan": bool(c.exit_plan) if c else False}


def _gaps(vendor: Vendor, c: Continuity | None) -> list[str]:
    reasons = []
    if not c or not c.plan_available:
        reasons.append("no continuity plan")
    if not c or not c.exit_plan:
        reasons.append("no exit/fallback plan")
    if not c or not c.last_test_date:
        reasons.append("never tested")
    elif c.last_test_date < date.today() - timedelta(days=365):
        reasons.append(f"last test {c.last_test_date} > 1yr ago")
    return reasons


@router.get("/continuity/report/gaps")
def gaps(user: User = Depends(VIEW), db: Session = Depends(get_db)):
    """WHY: critical = tier1 or High data access; gap = missing/untested plan."""
    out = []
    for v in db.query(Vendor).all():
        if not (v.tier == 1 or v.data_access == "High"):
            continue
        c = db.get(Continuity, v.id)
        reasons = _gaps(v, c)
        if reasons:
            out.append({"vendor_id": v.id, "name": v.name, "reasons": reasons})
    return out


@router.get("/continuity")
def list_all(user: User = Depends(VIEW), db: Session = Depends(get_db)):
    return [_out(v, db.get(Continuity, v.id)) for v in db.query(Vendor).all()]


@router.get("/continuity/{vid}")
def get_one(vid: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    v = db.get(Vendor, vid)
    if not v:
        raise HTTPException(status_code=404, detail="Not found")
    if user.role == "Vendor" and user.vendor_id != vid:
        raise HTTPException(status_code=403, detail="Vendor may see only own continuity")
    if user.role not in ("Admin", "Reviewer", "Auditor", "Vendor"):
        raise HTTPException(status_code=403, detail="Forbidden")
    return _out(v, db.get(Continuity, vid))


@router.put("/continuity/{vid}")
def upsert(vid: int, body: ContinuityUpdate, user: User = Depends(require_roles("Admin", "Reviewer")),
           request: Request = None, db: Session = Depends(get_db)):
    v = db.get(Vendor, vid)
    if not v:
        raise HTTPException(status_code=404, detail="Vendor not found")
    c = db.get(Continuity, vid)
    if not c:
        c = Continuity(vendor_id=vid)
        db.add(c)
    c.rto_hours, c.rpo_hours = body.rto_hours, body.rpo_hours
    c.plan_available, c.last_test_date, c.exit_plan = body.plan_available, body.last_test_date, body.exit_plan
    write_audit(db, user.id, "update", "continuity", vid, client_ip(request), {})
    db.commit()
    return _out(v, c)
