"""ITGC checklist + config change log. WHY: auditors need Pass/Fail + evidence."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.deps import require_roles
from app.core.rate_limit import client_ip
from app.db.session import get_db
from app.models.itgc import ConfigChange, ITGCCheck
from app.models.user import User
from app.schemas.governance import ConfigCreate, ITGCCreate, ITGCUpdate

router = APIRouter(tags=["itgc"])
VIEW = require_roles("Admin", "Reviewer", "Auditor")
EDIT = require_roles("Admin", "Reviewer")


@router.get("/itgc")
def list_itgc(user: User = Depends(VIEW), db: Session = Depends(get_db)):
    return [{"id": r.id, "domain": r.domain, "control": r.control,
             "evidence": r.evidence, "status": r.status}
            for r in db.query(ITGCCheck).all()]


@router.post("/itgc", status_code=201)
def create_itgc(body: ITGCCreate, user: User = Depends(EDIT),
                request: Request = None, db: Session = Depends(get_db)):
    # WHY: Pass without evidence is unauditable - reject like assessment answers.
    if body.status == "Pass" and len(body.evidence.strip()) < 3:
        raise HTTPException(status_code=422, detail="Evidence required for Pass")
    r = ITGCCheck(domain=body.domain, control=body.control, evidence=body.evidence, status=body.status)
    db.add(r)
    db.flush()
    write_audit(db, user.id, "create", "itgc", r.id, client_ip(request), {"domain": r.domain})
    db.commit()
    return {"id": r.id, "status": r.status}


@router.patch("/itgc/{iid}")
def update_itgc(iid: int, body: ITGCUpdate, user: User = Depends(EDIT),
                request: Request = None, db: Session = Depends(get_db)):
    r = db.get(ITGCCheck, iid)
    if not r:
        raise HTTPException(status_code=404, detail="Not found")
    new_status = body.status or r.status
    new_ev = body.evidence if body.evidence is not None else r.evidence
    if new_status == "Pass" and len((new_ev or "").strip()) < 3:
        raise HTTPException(status_code=422, detail="Evidence required for Pass")
    old = r.status
    r.status, r.evidence = new_status, new_ev
    write_audit(db, user.id, "update", "itgc", iid, client_ip(request), {"from": old, "to": new_status})
    db.commit()
    return {"id": r.id, "status": r.status}


@router.get("/config-changes")
def list_changes(user: User = Depends(VIEW), db: Session = Depends(get_db)):
    return [{"id": c.id, "changed_by": c.changed_by, "change": c.change}
            for c in db.query(ConfigChange).order_by(ConfigChange.id.desc()).limit(200).all()]


@router.post("/config-changes", status_code=201)
def log_change(body: ConfigCreate, user: User = Depends(require_roles("Admin")),
               request: Request = None, db: Session = Depends(get_db)):
    """WHY: Admin-only change log + audit = ITGC change-management proof."""
    c = ConfigChange(changed_by=user.id, change=body.change)
    db.add(c)
    db.flush()
    write_audit(db, user.id, "config_change", "config", c.id, client_ip(request), {"change": body.change[:200]})
    db.commit()
    return {"id": c.id}
