"""Incidents. WHY: strict lifecycle stops skipping containment."""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.deps import get_current_user, require_roles
from app.core.rate_limit import client_ip
from app.db.session import get_db
from app.models.monitoring import Incident, IncidentNote
from app.models.user import User
from app.models.vendor import Vendor

router = APIRouter(tags=["incidents"])
VIEW = require_roles("Admin", "Reviewer", "Auditor")
EDIT = require_roles("Admin", "Reviewer")

FLOW = ["Detected", "Triaged", "Contained", "Eradicated", "Recovered", "LessonsLearned"]


class IncidentCreate(BaseModel):
    title: str = Field(min_length=5, max_length=255)
    vendor_id: int | None = None
    severity: str = Field(default="Medium", pattern="^(Low|Medium|High|Critical)$")


class TransitionIn(BaseModel):
    to: str = Field(pattern="^(Detected|Triaged|Contained|Eradicated|Recovered|LessonsLearned)$")


class NoteIn(BaseModel):
    note: str = Field(min_length=3, max_length=5000)


@router.get("/incidents")
def list_incidents(user: User = Depends(VIEW), db: Session = Depends(get_db)):
    return [{"id": i.id, "title": i.title, "vendor_id": i.vendor_id,
             "severity": i.severity, "status": i.status}
            for i in db.query(Incident).order_by(Incident.id.desc()).all()]


@router.post("/incidents", status_code=201)
def create_incident(body: IncidentCreate, user: User = Depends(EDIT),
                    request: Request = None, db: Session = Depends(get_db)):
    if body.vendor_id and not db.get(Vendor, body.vendor_id):
        raise HTTPException(status_code=404, detail="Vendor not found")
    inc = Incident(title=body.title, vendor_id=body.vendor_id, severity=body.severity, status="Detected")
    db.add(inc)
    db.flush()
    db.add(IncidentNote(incident_id=inc.id, note=f"SAMPLE: opened by {user.email} - Detected"))
    write_audit(db, user.id, "create", "incident", inc.id, client_ip(request), {"title": body.title})
    db.commit()
    return {"id": inc.id, "status": "Detected"}


@router.get("/incidents/{iid}")
def get_incident(iid: int, user: User = Depends(VIEW), db: Session = Depends(get_db)):
    inc = db.get(Incident, iid)
    if not inc:
        raise HTTPException(status_code=404, detail="Not found")
    notes = db.query(IncidentNote).filter_by(incident_id=iid).order_by(IncidentNote.id).all()
    return {"id": inc.id, "title": inc.title, "vendor_id": inc.vendor_id,
            "severity": inc.severity, "status": inc.status,
            "timeline": [{"id": n.id, "note": n.note, "at": str(n.created_at)} for n in notes]}


@router.post("/incidents/{iid}/transition")
def transition(iid: int, body: TransitionIn, user: User = Depends(EDIT),
               request: Request = None, db: Session = Depends(get_db)):
    inc = db.get(Incident, iid)
    if not inc:
        raise HTTPException(status_code=404, detail="Not found")
    # WHY: only next step (or same) allowed - no skipping containment.
    cur, nxt = FLOW.index(inc.status), FLOW.index(body.to)
    if nxt not in (cur, cur + 1):
        raise HTTPException(status_code=400, detail=f"Must move stepwise, now {inc.status}")
    old = inc.status
    inc.status = body.to
    db.add(IncidentNote(incident_id=iid, note=f"{old}->{body.to} by {user.email}"))
    write_audit(db, user.id, "transition", "incident", iid, client_ip(request), {"from": old, "to": body.to})
    db.commit()
    return {"id": inc.id, "status": inc.status}


@router.post("/incidents/{iid}/notes", status_code=201)
def add_note(iid: int, body: NoteIn, user: User = Depends(EDIT),
             request: Request = None, db: Session = Depends(get_db)):
    if not db.get(Incident, iid):
        raise HTTPException(status_code=404, detail="Not found")
    n = IncidentNote(incident_id=iid, note=body.note)
    db.add(n)
    db.flush()
    write_audit(db, user.id, "create", "incident_note", n.id, client_ip(request), {"incident": iid})
    db.commit()
    return {"id": n.id}
