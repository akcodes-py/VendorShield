"""Questionnaire + scoring. WHY: weights + evidence rules = defensible risk rating."""
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.deps import get_current_user, require_roles
from app.core.rate_limit import client_ip
from app.db.session import get_db
from app.models.assessment import Answer, Assessment, Question
from app.models.user import User
from app.models.vendor import Vendor
from app.schemas.vendor import AnswersIn
from app.services.remediation import suggestions
from app.services.scoring import level_for, weighted_score

router = APIRouter(tags=["assessments"])

VALID = {"Yes", "Partial", "No", "N/A"}


def _vendor_scope(user: User, vendor_id: int):
    if user.role == "Vendor" and user.vendor_id != vendor_id:
        raise HTTPException(status_code=403, detail="Vendor may access only own questionnaire")


@router.get("/questions")
def list_questions(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [{"id": q.id, "domain": q.domain, "text": q.text, "weight": q.weight}
            for q in db.query(Question).order_by(Question.id).all()]


@router.post("/vendors/{vid}/assessments", status_code=201)
def create_assessment(vid: int, user: User = Depends(require_roles("Admin", "Reviewer")),
                      request: Request = None, db: Session = Depends(get_db)):
    v = db.get(Vendor, vid)
    if not v:
        raise HTTPException(status_code=404, detail="Vendor not found")
    a = Assessment(vendor_id=vid, assessor_id=user.id, status="draft")
    db.add(a)
    db.flush()
    write_audit(db, user.id, "create", "assessment", a.id, client_ip(request), {"vendor": vid})
    db.commit()
    return {"id": a.id, "vendor_id": vid, "status": "draft"}


@router.get("/assessments/{aid}")
def get_assessment(aid: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    a = db.get(Assessment, aid)
    if not a:
        raise HTTPException(status_code=404, detail="Not found")
    _vendor_scope(user, a.vendor_id)
    ans = db.query(Answer).filter_by(assessment_id=aid).all()
    return {"id": a.id, "vendor_id": a.vendor_id, "status": a.status,
            "overall_score": a.overall_score, "risk_level": a.risk_level,
            "answers": [{"question_id": x.question_id, "value": x.value, "evidence": x.evidence} for x in ans]}


@router.put("/assessments/{aid}/answers")
def put_answers(aid: int, body: AnswersIn,
                user: User = Depends(require_roles("Admin", "Reviewer", "Vendor")),
                request: Request = None, db: Session = Depends(get_db)):
    a = db.get(Assessment, aid)
    if not a or a.status != "draft":
        raise HTTPException(status_code=404, detail="Draft assessment not found")
    _vendor_scope(user, a.vendor_id)
    for item in body.answers:
        if item.value not in VALID:
            raise HTTPException(status_code=422, detail=f"Bad value {item.value}")
        # WHY: No/Partial without evidence is unauditable - reject.
        if item.value in ("No", "Partial") and len(item.evidence.strip()) < 3:
            raise HTTPException(status_code=422, detail=f"Evidence required for {item.value} Q{item.question_id}")
        q = db.get(Question, item.question_id)
        if not q:
            raise HTTPException(status_code=404, detail=f"Q{item.question_id} missing")
        ex = db.query(Answer).filter_by(assessment_id=aid, question_id=item.question_id).first()
        if ex:
            ex.value, ex.evidence = item.value, item.evidence
        else:
            db.add(Answer(assessment_id=aid, question_id=item.question_id, value=item.value, evidence=item.evidence))
    write_audit(db, user.id, "update", "assessment", aid, client_ip(request), {"answers": len(body.answers)})
    db.commit()
    return {"status": "saved", "count": len(body.answers)}


@router.post("/assessments/{aid}/submit")
def submit(aid: int, user: User = Depends(require_roles("Admin", "Reviewer")),
           request: Request = None, db: Session = Depends(get_db)):
    """WHY: only Reviewer/Admin submit - Vendor answers, Reviewer rates (SoD)."""
    a = db.get(Assessment, aid)
    if not a or a.status != "draft":
        raise HTTPException(status_code=404, detail="Draft not found")
    rows = db.query(Answer, Question).join(Question, Answer.question_id == Question.id)\
        .filter(Answer.assessment_id == aid).all()
    if not rows:
        raise HTTPException(status_code=400, detail="No answers yet")

    by_domain: dict[str, list] = defaultdict(list)
    for ans, q in rows:
        by_domain[q.domain].append((q.weight, ans.value))

    domain_scores = {}
    failed, partial = set(), set()
    for dom, pairs in by_domain.items():
        s = weighted_score(pairs)
        domain_scores[dom] = s
        if s < 40:
            failed.add(dom)
        elif s < 85:
            partial.add(dom)

    overall = weighted_score([(q.weight, an.value) for an, q in rows])
    a.overall_score, a.risk_level, a.status = overall, level_for(overall), "submitted"
    # failed questions detail
    failed_qs = [{"question_id": q.id, "domain": q.domain, "text": q.text}
                 for an, q in rows if an.value == "No"]
    rem = suggestions(failed, partial)
    write_audit(db, user.id, "submit", "assessment", aid, client_ip(request), {"score": overall})
    db.commit()
    return {"overall_score": overall, "risk_level": a.risk_level,
            "domain_scores": domain_scores, "failed_controls": failed_qs,
            "remediation": rem}
