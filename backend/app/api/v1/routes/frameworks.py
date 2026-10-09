"""Framework mapping + coverage %. WHY: proves questionnaire actually covers ISO/NIST."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.deps import get_current_user, require_roles
from app.core.rate_limit import client_ip
from app.db.session import get_db
from app.models.assessment import Question
from app.models.policy import FrameworkControl, QuestionControlMap
from app.models.user import User
from app.schemas.governance import MapIn

router = APIRouter(tags=["frameworks"])
VIEW = require_roles("Admin", "Reviewer", "Auditor")


@router.get("/frameworks/controls")
def list_controls(framework: str | None = None, user: User = Depends(VIEW),
                  db: Session = Depends(get_db)):
    q = db.query(FrameworkControl)
    if framework:
        q = q.filter_by(framework=framework)
    return [{"id": c.id, "framework": c.framework, "control_id": c.control_id, "title": c.title}
            for c in q.all()]


@router.post("/frameworks/map", status_code=201)
def map_qc(body: MapIn, user: User = Depends(require_roles("Admin", "Reviewer")),
           request: Request = None, db: Session = Depends(get_db)):
    if not db.get(Question, body.question_id) or not db.get(FrameworkControl, body.control_id):
        raise HTTPException(status_code=404, detail="Question or control missing")
    if db.query(QuestionControlMap).filter_by(question_id=body.question_id, control_id=body.control_id).first():
        raise HTTPException(status_code=409, detail="Mapping exists")
    m = QuestionControlMap(question_id=body.question_id, control_id=body.control_id)
    db.add(m)
    db.flush()
    write_audit(db, user.id, "create", "mapping", m.id, client_ip(request), {})
    db.commit()
    return {"id": m.id}


@router.get("/frameworks/coverage")
def coverage(framework: str, user: User = Depends(VIEW), db: Session = Depends(get_db)):
    """WHY: coverage = controls linked to >=1 question / total. Unmapped = gap."""
    ctrls = db.query(FrameworkControl).filter_by(framework=framework).all()
    if not ctrls:
        raise HTTPException(status_code=404, detail="Framework has no controls")
    mapped_ids = {m.control_id for m in db.query(QuestionControlMap).all()
                  if db.get(FrameworkControl, m.control_id) and
                  db.get(FrameworkControl, m.control_id).framework == framework}
    total, mapped = len(ctrls), len([c for c in ctrls if c.id in mapped_ids])
    pct = round(mapped / total * 100, 1) if total else 0.0
    unmapped = [c.control_id for c in ctrls if c.id not in mapped_ids]
    return {"framework": framework, "total": total, "mapped": mapped,
            "coverage_pct": pct, "unmapped": unmapped}
