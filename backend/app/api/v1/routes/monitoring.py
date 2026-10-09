"""Events + alerts. WHY: Vendor has no SOC access (least privilege)."""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.deps import require_roles
from app.core.rate_limit import client_ip
from app.db.session import get_db
from app.models.monitoring import Alert, SecurityEvent
from app.models.user import User
from app.services.detection import log_event, run_rules

router = APIRouter(tags=["monitoring"])
VIEW = require_roles("Admin", "Reviewer", "Auditor")
EDIT = require_roles("Admin", "Reviewer")


class EventIn(BaseModel):
    type: str = Field(pattern="^(failed_login|login_success|perm_denied|privilege_change|suspicious_upload|other)$")
    user_id: int | None = None
    ip: str = ""
    detail: str = ""


class TriageIn(BaseModel):
    status: str = Field(pattern="^(New|Investigating|Resolved|FalsePositive)$")


@router.get("/security-events")
def list_events(user: User = Depends(VIEW), db: Session = Depends(get_db)):
    rows = db.query(SecurityEvent).order_by(SecurityEvent.id.desc()).limit(200).all()
    return [{"id": e.id, "type": e.type, "user_id": e.user_id, "ip": e.ip,
             "detail": e.detail, "is_sample": bool(e.is_sample),
             "created_at": str(e.created_at)} for e in rows]


@router.post("/security-events", status_code=201)
def create_event(body: EventIn, user: User = Depends(EDIT),
                 request: Request = None, db: Session = Depends(get_db)):
    # WHY: manual log lets tests + simulation feed the rules honestly.
    e = log_event(db, body.type, body.user_id, body.ip or client_ip(request), body.detail, 0)
    write_audit(db, user.id, "create", "security_event", e.id, client_ip(request), {"type": body.type})
    db.commit()
    return {"id": e.id}


@router.post("/detection/run")
def run_detection(user: User = Depends(EDIT),
                  request: Request = None, db: Session = Depends(get_db)):
    alerts = run_rules(db)
    write_audit(db, user.id, "detection_run", "alert", None, client_ip(request), {"new": len(alerts)})
    db.commit()
    return [{"id": a.id, "rule": a.rule, "severity": a.severity, "detail": a.detail} for a in alerts]


@router.get("/alerts")
def list_alerts(status: str | None = None, user: User = Depends(VIEW), db: Session = Depends(get_db)):
    q = db.query(Alert).order_by(Alert.id.desc())
    if status:
        q = q.filter_by(status=status)
    return [{"id": a.id, "rule": a.rule, "severity": a.severity,
             "status": a.status, "detail": a.detail} for a in q.limit(200).all()]


@router.patch("/alerts/{aid}")
def triage(aid: int, body: TriageIn, user: User = Depends(EDIT),
           request: Request = None, db: Session = Depends(get_db)):
    a = db.get(Alert, aid)
    if not a:
        raise HTTPException(status_code=404, detail="Not found")
    old = a.status
    a.status = body.status
    write_audit(db, user.id, "update", "alert", aid, client_ip(request), {"from": old, "to": body.status})
    db.commit()
    return {"id": a.id, "status": a.status}
