"""Risks + remediations + exceptions. WHY: residual<=inherent + audit every change."""
from collections import Counter
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.deps import get_current_user, require_roles
from app.core.rate_limit import client_ip
from app.db.session import get_db
from app.models.risk import Remediation, Risk, RiskException
from app.models.user import User
from app.models.vendor import Vendor
from app.models.workflow import Approval
from app.schemas.risk import RemediationCreate, RemediationUpdate, RiskCreate, RiskUpdate
from app.services.risks import heatmap, inherent, is_overdue, severity

router = APIRouter(tags=["risks"])


class ExceptionIn(BaseModel):
    justification: str = Field(min_length=10)
    expiry_date: date | None = None


def _scope(user: User, vendor_id: int):
    if user.role == "Vendor" and user.vendor_id != vendor_id:
        raise HTTPException(status_code=403, detail="Vendor may see only own risks")


def _rout(r: Risk) -> dict:
    od = is_overdue(r.due_date, r.status)
    return {"id": r.id, "vendor_id": r.vendor_id, "description": r.description,
            "category": r.category, "likelihood": r.likelihood, "impact": r.impact,
            "inherent_score": r.inherent_score, "severity": severity(r.inherent_score),
            "controls": r.controls, "residual_score": r.residual_score,
            "owner": r.owner, "status": r.status,
            "due_date": str(r.due_date) if r.due_date else None, "overdue": od}


@router.get("/risks/heatmap")
def risk_heatmap(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(Risk).filter(Risk.status.in_(["open", "mitigating"]))
    if user.role == "Vendor":
        q = q.filter_by(vendor_id=user.vendor_id)
    c = Counter((r.likelihood, r.impact) for r in q.all())
    return heatmap(dict(c))


@router.get("/risks")
def list_risks(vendor_id: int | None = None, status: str | None = None, overdue: bool | None = None,
               user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(Risk)
    if user.role == "Vendor":
        q = q.filter_by(vendor_id=user.vendor_id)
    elif vendor_id is not None:
        q = q.filter_by(vendor_id=vendor_id)
    if status:
        q = q.filter_by(status=status)
    rows = [_rout(r) for r in q.all()]
    if overdue is True:
        rows = [r for r in rows if r["overdue"]]
    return rows


@router.post("/risks", status_code=201)
def create_risk(body: RiskCreate, user: User = Depends(require_roles("Admin", "Reviewer")),
                request: Request = None, db: Session = Depends(get_db)):
    if not db.get(Vendor, body.vendor_id):
        raise HTTPException(status_code=404, detail="Vendor not found")
    inh = inherent(body.likelihood, body.impact)
    r = Risk(vendor_id=body.vendor_id, description=body.description, category=body.category,
             likelihood=body.likelihood, impact=body.impact, inherent_score=inh,
             controls=body.controls, residual_score=inh, owner=body.owner,
             status="open", due_date=body.due_date)
    db.add(r)
    db.flush()
    write_audit(db, user.id, "create", "risk", r.id, client_ip(request), {"inherent": inh})
    db.commit()
    return _rout(r)


@router.get("/risks/{rid}")
def get_risk(rid: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    r = db.get(Risk, rid)
    if not r:
        raise HTTPException(status_code=404, detail="Not found")
    _scope(user, r.vendor_id)
    return _rout(r)


@router.patch("/risks/{rid}")
def update_risk(rid: int, body: RiskUpdate, user: User = Depends(require_roles("Admin", "Reviewer")),
                request: Request = None, db: Session = Depends(get_db)):
    r = db.get(Risk, rid)
    if not r:
        raise HTTPException(status_code=404, detail="Not found")
    old = {"l": r.likelihood, "i": r.impact, "res": r.residual_score, "status": r.status}
    if body.description is not None:
        r.description = body.description
    if body.category is not None:
        r.category = body.category
    if body.likelihood is not None:
        r.likelihood = body.likelihood
    if body.impact is not None:
        r.impact = body.impact
    # WHY: LxI change recomputes inherent; residual capped to new inherent.
    r.inherent_score = inherent(r.likelihood, r.impact)
    if r.residual_score > r.inherent_score:
        r.residual_score = r.inherent_score
    if body.controls is not None:
        r.controls = body.controls
    if body.residual_score is not None:
        # WHY: residual < inherent needs controls proof, else 400.
        if body.residual_score > r.inherent_score:
            raise HTTPException(status_code=400, detail="Residual cannot exceed inherent")
        if body.residual_score < r.inherent_score and not (body.controls or r.controls):
            raise HTTPException(status_code=400, detail="Controls required to claim reduction")
        r.residual_score = body.residual_score
    if body.owner is not None:
        r.owner = body.owner
    if body.status is not None:
        r.status = body.status
    if body.due_date is not None:
        r.due_date = body.due_date
    write_audit(db, user.id, "update", "risk", rid, client_ip(request), {"old": old, "new": r.inherent_score})
    db.commit()
    return _rout(r)


# --- Remediations ---
@router.post("/risks/{rid}/remediations", status_code=201)
def add_rem(rid: int, body: RemediationCreate, user: User = Depends(require_roles("Admin", "Reviewer")),
            request: Request = None, db: Session = Depends(get_db)):
    r = db.get(Risk, rid)
    if not r:
        raise HTTPException(status_code=404, detail="Risk not found")
    m = Remediation(risk_id=rid, action=body.action, owner=body.owner, due_date=body.due_date, status="open")
    db.add(m)
    db.flush()
    write_audit(db, user.id, "create", "remediation", m.id, client_ip(request), {"risk": rid})
    db.commit()
    return {"id": m.id, "risk_id": rid, "action": m.action, "status": m.status,
            "due_date": str(m.due_date) if m.due_date else None,
            "overdue": is_overdue(m.due_date, m.status if m.status != "done" else "closed")}


@router.get("/risks/{rid}/remediations")
def list_rem(rid: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    r = db.get(Risk, rid)
    if not r:
        raise HTTPException(status_code=404, detail="Not found")
    _scope(user, r.vendor_id)
    out = []
    for m in db.query(Remediation).filter_by(risk_id=rid).all():
        od = m.due_date and m.due_date < date.today() and m.status != "done"
        out.append({"id": m.id, "action": m.action, "owner": m.owner,
                    "due_date": str(m.due_date) if m.due_date else None,
                    "status": m.status, "overdue": bool(od)})
    return out


@router.patch("/remediations/{mid}")
def update_rem(mid: int, body: RemediationUpdate, user: User = Depends(require_roles("Admin", "Reviewer")),
               request: Request = None, db: Session = Depends(get_db)):
    m = db.get(Remediation, mid)
    if not m:
        raise HTTPException(status_code=404, detail="Not found")
    old = m.status
    m.status = body.status
    write_audit(db, user.id, "update", "remediation", mid, client_ip(request), {"from": old, "to": body.status})
    db.commit()
    return {"id": m.id, "status": m.status}


# --- Exceptions: accept risk with expiry, needs Admin approval ---
@router.post("/risks/{rid}/exceptions", status_code=201)
def request_exception(rid: int, body: ExceptionIn, user: User = Depends(require_roles("Admin", "Reviewer")),
                      request: Request = None, db: Session = Depends(get_db)):
    r = db.get(Risk, rid)
    if not r:
        raise HTTPException(status_code=404, detail="Risk not found")
    ex = RiskException(risk_id=rid, justification=body.justification,
                       expiry_date=body.expiry_date, requested_by=user.id, status="Pending")
    db.add(ex)
    db.flush()
    ap = Approval(entity_type="exception", entity_id=ex.id, requested_by=user.id, decision="Pending")
    db.add(ap)
    db.flush()
    write_audit(db, user.id, "exception_request", "risk", rid, client_ip(request), {"exception": ex.id})
    db.commit()
    return {"exception_id": ex.id, "approval_id": ap.id, "status": "Pending - needs Admin"}
