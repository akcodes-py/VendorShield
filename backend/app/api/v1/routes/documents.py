"""Documents: secure upload + review + expiry. WHY: random names + header checks."""
from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.deps import get_current_user, require_roles
from app.core.rate_limit import client_ip
from app.db.session import get_db
from app.models.document import Document
from app.models.user import User
from app.models.vendor import Vendor
from app.schemas.document import ReviewIn
from app.services.ai_summary import RISKS_NOTE, draft_for
from app.services.detection import log_event
from app.services.documents import expiry_flag, save_random, validate_file

router = APIRouter(tags=["documents"])

DOC_TYPES = {"ISO27001", "SOC2", "Policy", "Pentest"}


def _scope(user: User, vendor_id: int):
    if user.role == "Vendor" and user.vendor_id != vendor_id:
        raise HTTPException(status_code=403, detail="Vendor may access only own docs")


def _out(d: Document) -> dict:
    return {"id": d.id, "vendor_id": d.vendor_id, "doc_type": d.doc_type,
            "original_name": d.original_name, "mime": d.mime, "size_bytes": d.size_bytes,
            "issue_date": str(d.issue_date) if d.issue_date else None,
            "expiry_date": str(d.expiry_date) if d.expiry_date else None,
            "expiry_flag": expiry_flag(d.expiry_date),
            "review_status": d.review_status, "review_notes": d.review_notes,
            "ai_summary": d.ai_summary, "ai_confirmed": bool(d.ai_confirmed)}


def _parse(d: str | None) -> date | None:
    return date.fromisoformat(d) if d else None


@router.post("/documents/upload", status_code=201)
async def upload(vendor_id: int = Form(...), doc_type: str = Form(...),
                 issue_date: str | None = Form(None), expiry_date: str | None = Form(None),
                 file: UploadFile = File(...),
                 user: User = Depends(require_roles("Admin", "Reviewer", "Vendor")),
                 request: Request = None, db: Session = Depends(get_db)):
    if doc_type not in DOC_TYPES:
        raise HTTPException(status_code=422, detail=f"doc_type must be {DOC_TYPES}")
    v = db.get(Vendor, vendor_id)
    if not v:
        raise HTTPException(status_code=404, detail="Vendor not found")
    _scope(user, vendor_id)
    data = await file.read()
    try:
        ext = validate_file(file.filename or "", file.content_type or "", data)
    except ValueError as e:
        # WHY: SOC fact for upload-probing review.
        log_event(db, "suspicious_upload", user.id, client_ip(request),
                  f"file={file.filename} mime={file.content_type}: {e}")
        db.commit()
        raise HTTPException(status_code=400, detail=str(e))
    stored = save_random(data, ext)
    d = Document(vendor_id=vendor_id, doc_type=doc_type, stored_name=stored,
                 original_name=(file.filename or "")[:255], mime=file.content_type or "",
                 size_bytes=len(data), issue_date=_parse(issue_date), expiry_date=_parse(expiry_date))
    db.add(d)
    db.flush()
    write_audit(db, user.id, "create", "document", d.id, client_ip(request),
                {"vendor": vendor_id, "type": doc_type})
    db.commit()
    return _out(d)


@router.get("/documents")
def list_docs(vendor_id: int | None = None, status: str | None = None,
              user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # WHY: Vendor sees only own; status filter Valid|Expiring|Expired for dashboard.
    q = db.query(Document)
    if user.role == "Vendor":
        q = q.filter_by(vendor_id=user.vendor_id)
    elif vendor_id is not None:
        q = q.filter_by(vendor_id=vendor_id)
    rows = [_out(d) for d in q.all()]
    if status:
        rows = [r for r in rows if r["expiry_flag"] == status]
    return rows


@router.get("/documents/{did}")
def get_doc(did: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    d = db.get(Document, did)
    if not d:
        raise HTTPException(status_code=404, detail="Not found")
    _scope(user, d.vendor_id)
    return _out(d)


@router.patch("/documents/{did}/review")
def review(did: int, body: ReviewIn, user: User = Depends(require_roles("Admin", "Reviewer")),
           request: Request = None, db: Session = Depends(get_db)):
    d = db.get(Document, did)
    if not d:
        raise HTTPException(status_code=404, detail="Not found")
    old = d.review_status
    d.review_status, d.review_notes, d.reviewer_id = body.review_status, body.review_notes, user.id
    write_audit(db, user.id, "update", "document", did, client_ip(request), {"review": [old, body.review_status]})
    db.commit()
    return _out(d)


@router.post("/documents/{did}/ai-summary")
def ai_summary(did: int, user: User = Depends(require_roles("Admin", "Reviewer")),
               request: Request = None, db: Session = Depends(get_db)):
    d = db.get(Document, did)
    if not d:
        raise HTTPException(status_code=404, detail="Not found")
    try:
        draft, _ = draft_for(d)
    except RuntimeError as e:
        # WHY: honest 400 + risks note, never fake AI output.
        raise HTTPException(status_code=400, detail=str(e) + " | " + RISKS_NOTE)
    d.ai_summary, d.ai_confirmed = draft, 0
    write_audit(db, user.id, "ai_draft", "document", did, client_ip(request), {})
    db.commit()
    return {"ai_summary": draft, "note": RISKS_NOTE}


@router.post("/documents/{did}/ai-confirm")
def ai_confirm(did: int, user: User = Depends(require_roles("Admin", "Reviewer")),
               request: Request = None, db: Session = Depends(get_db)):
    """WHY: human must confirm AI draft before it counts."""
    d = db.get(Document, did)
    if not d or not d.ai_summary:
        raise HTTPException(status_code=404, detail="No AI draft to confirm")
    d.ai_confirmed = 1
    write_audit(db, user.id, "ai_confirm", "document", did, client_ip(request), {})
    db.commit()
    return _out(d)
