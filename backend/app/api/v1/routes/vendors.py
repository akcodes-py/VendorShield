"""Vendors CRUD + lifecycle. WHY: tier->frequency + RBAC scoping enforced here."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.deps import get_current_user, require_roles
from app.core.rate_limit import client_ip
from app.db.session import get_db
from app.models.user import User
from app.models.vendor import Vendor
from app.models.workflow import Approval as ApprovalModel
from app.schemas.vendor import TransitionIn, VendorCreate, VendorUpdate
from app.services.lifecycle import can_transition, next_review

router = APIRouter(tags=["vendors"])


def _out(v: Vendor) -> dict:
    return {"id": v.id, "name": v.name, "service_type": v.service_type,
            "data_access": v.data_access, "tier": v.tier, "lifecycle": v.lifecycle,
            "contact_name": v.contact_name, "contact_email": v.contact_email,
            "freq_months": v.freq_months, "next_review_date": str(v.next_review_date) if v.next_review_date else None}


def _scope_check(user: User, vendor_id: int):
    # WHY: Vendor role sees only own vendor (IDOR guard).
    if user.role == "Vendor" and user.vendor_id != vendor_id:
        raise HTTPException(status_code=403, detail="Vendor may see only own record")


@router.get("/vendors")
def list_vendors(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role == "Vendor":
        vs = db.query(Vendor).filter_by(id=user.vendor_id).all() if user.vendor_id else []
    else:
        vs = db.query(Vendor).all()
    return [_out(v) for v in vs]


@router.post("/vendors", status_code=201)
def create_vendor(body: VendorCreate, user: User = Depends(require_roles("Admin", "Reviewer")),
                  request: Request = None, db: Session = Depends(get_db)):
    freq, nxt = next_review(date.today(), body.tier)  # WHY: auto frequency by tier
    v = Vendor(name=body.name, service_type=body.service_type, data_access=body.data_access,
               tier=body.tier, contact_name=body.contact_name, contact_email=body.contact_email,
               lifecycle="Onboarding", onboarding_date=date.today(),
               freq_months=freq, next_review_date=nxt)
    db.add(v)
    db.flush()
    write_audit(db, user.id, "create", "vendor", v.id, client_ip(request), {"name": v.name, "tier": v.tier})
    db.commit()
    return _out(v)


@router.get("/vendors/{vid}")
def get_vendor(vid: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    v = db.get(Vendor, vid)
    if not v:
        raise HTTPException(status_code=404, detail="Not found")
    _scope_check(user, vid)
    return _out(v)


@router.patch("/vendors/{vid}")
def update_vendor(vid: int, body: VendorUpdate, user: User = Depends(require_roles("Admin", "Reviewer")),
                  request: Request = None, db: Session = Depends(get_db)):
    v = db.get(Vendor, vid)
    if not v:
        raise HTTPException(status_code=404, detail="Not found")
    old = {"tier": v.tier, "name": v.name}
    for f in ("name", "service_type", "data_access", "tier", "contact_name", "contact_email"):
        val = getattr(body, f)
        if val is not None:
            setattr(v, f, val)
    if body.tier is not None:  # WHY: tier change recalculates review cadence
        freq, nxt = next_review(v.onboarding_date, v.tier)
        v.freq_months, v.next_review_date = freq, nxt
    write_audit(db, user.id, "update", "vendor", vid, client_ip(request), {"old": old, "new": {"tier": v.tier}})
    db.commit()
    return _out(v)


@router.post("/vendors/{vid}/transition")
def transition(vid: int, body: TransitionIn, user: User = Depends(require_roles("Admin", "Reviewer")),
               request: Request = None, db: Session = Depends(get_db)):
    v = db.get(Vendor, vid)
    if not v:
        raise HTTPException(status_code=404, detail="Not found")
    ok, why = can_transition(v.lifecycle, body.to, user.role)
    if not ok:
        raise HTTPException(status_code=400, detail=why)
    old = v.lifecycle
    v.lifecycle = body.to
    if body.to == "Approved":  # WHY: approval resets review clock
        freq, nxt = next_review(date.today(), v.tier)
        v.freq_months, v.next_review_date = freq, nxt
    write_audit(db, user.id, "transition", "vendor", vid, client_ip(request), {"from": old, "to": body.to})
    db.commit()
    # WHY: every state change needs audit trail (GRC requirement).
    db.add(ApprovalModel(entity_type="vendor_lifecycle", entity_id=vid, requested_by=user.id,
                         decided_by=user.id, decision="Approved", comments=f"{old}->{body.to}"))
    db.commit()
    return _out(v)


@router.post("/vendors/{vid}/delete-request", status_code=201)
def delete_request(vid: int, user: User = Depends(require_roles("Admin")),
                   request: Request = None, db: Session = Depends(get_db)):
    """WHY: privileged delete needs 2nd Admin - only creates request here."""
    v = db.get(Vendor, vid)
    if not v:
        raise HTTPException(status_code=404, detail="Not found")
    ap = ApprovalModel(entity_type="vendor_delete", entity_id=vid, requested_by=user.id, decision="Pending")
    db.add(ap)
    db.flush()
    write_audit(db, user.id, "delete_request", "vendor", vid, client_ip(request), {})
    db.commit()
    return {"approval_id": ap.id, "status": "Pending - needs 2nd Admin"}
