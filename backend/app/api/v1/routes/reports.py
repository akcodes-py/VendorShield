"""Reports: dashboard JSON + PDFs. WHY: Vendor scoped, exec summary staff-only."""
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.user import User
from app.models.vendor import Vendor
from app.services.reporting import dashboard_data, executive_pdf, vendor_pdf

router = APIRouter(tags=["reports"])


@router.get("/reports/dashboard")
def dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    scope = user.vendor_id if user.role == "Vendor" else None
    return dashboard_data(db, scope)


@router.get("/reports/vendor/{vid}.pdf")
def vendor_report(vid: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role == "Vendor" and user.vendor_id != vid:
        raise HTTPException(status_code=403, detail="Vendor may export only own report")
    if not db.get(Vendor, vid):
        raise HTTPException(status_code=404, detail="Not found")
    pdf = vendor_pdf(db, vid)
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=vendor-{vid}.pdf"})


@router.get("/reports/executive.pdf")
def executive(user: User = Depends(require_roles("Admin", "Reviewer", "Auditor")),
              db: Session = Depends(get_db)):
    pdf = executive_pdf(db)
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": "attachment; filename=executive.pdf"})
