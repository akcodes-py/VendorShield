"""Approvals. WHY: 2nd Admin must decide; requester cannot self-approve."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.deps import require_admin
from app.core.rate_limit import client_ip
from app.db.session import get_db
from app.models.workflow import Approval
from app.models.user import User
from app.schemas.auth import DecideIn
from app.services.detection import log_event

router = APIRouter(tags=["approvals"])


@router.get("/approvals")
def list_approvals(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(Approval).order_by(Approval.id.desc()).all()
    return [{"id": r.id, "entity": f"{r.entity_type}:{r.entity_id}",
             "requested_by": r.requested_by, "decision": r.decision,
             "comments": r.comments} for r in rows]


@router.post("/approvals/{aid}/decide")
def decide(aid: int, body: DecideIn, admin: User = Depends(require_admin),
           request: Request = None, db: Session = Depends(get_db)):
    ap = db.get(Approval, aid)
    if not ap or ap.decision != "Pending":
        raise HTTPException(status_code=404, detail="Approval not found/closed")
    # WHY: SoD - same Admin cannot request + approve.
    if ap.requested_by == admin.id:
        raise HTTPException(status_code=403, detail="Second Admin required (SoD)")
    ap.decision = "Approved" if body.approve else "Rejected"
    ap.decided_by = admin.id
    ap.comments = (ap.comments or "") + f" | decided:{body.comments}"

    # Apply role change only on approval.
    if ap.entity_type == "role_change" and body.approve:
        # comments format "...|new_role=X"
        new_role = ap.comments.split("new_role=")[-1].split("|")[0].strip()
        target = db.get(User, ap.entity_id)
        if target:
            old = target.role
            target.role = new_role
            log_event(db, "privilege_change", target.id, client_ip(request),
                      f"role {old}->{new_role} by admin {admin.id}")
            write_audit(db, admin.id, "role_change", "user", target.id,
                        client_ip(request), {"role": [old, new_role]})

    # WHY: hard delete only if no history; else offboard (keeps audit trail).
    if ap.entity_type == "vendor_delete" and body.approve:
        from app.models.assessment import Assessment
        from app.models.document import Document
        from app.models.risk import Risk
        from app.models.vendor import Vendor
        v = db.get(Vendor, ap.entity_id)
        if not v:
            raise HTTPException(status_code=404, detail="Vendor gone")
        has_history = (
            db.query(Assessment).filter_by(vendor_id=v.id).count()
            + db.query(Document).filter_by(vendor_id=v.id).count()
            + db.query(Risk).filter_by(vendor_id=v.id).count()
        )
        if has_history:
            raise HTTPException(status_code=400, detail="Has history - offboard instead of delete")
        write_audit(db, admin.id, "delete", "vendor", v.id, client_ip(request), {"name": v.name})
        db.delete(v)

    write_audit(db, admin.id, "approval_decide", "approval", ap.id,
                client_ip(request), {"decision": ap.decision})
    # WHY: exception approval flips both exception + risk (accept with expiry).
    if ap.entity_type == "exception":
        from app.models.risk import RiskException, Risk
        ex = db.get(RiskException, ap.entity_id)
        if ex:
            ex.status = "Approved" if body.approve else "Rejected"
            if body.approve:
                rk = db.get(Risk, ex.risk_id)
                if rk:
                    rk.status = "accepted"
                    write_audit(db, admin.id, "exception_approve", "risk", rk.id,
                                client_ip(request), {"exception": ex.id})
    db.commit()
    return {"id": ap.id, "decision": ap.decision}
