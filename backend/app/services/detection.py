"""Detection rules. WHY: facts (events) -> alerts; dedupe stops alert storms."""
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.monitoring import Alert, SecurityEvent


def log_event(db: Session, etype: str, user_id: int | None = None,
              ip: str = "", detail: str = "", is_sample: int = 0) -> SecurityEvent:
    e = SecurityEvent(type=etype, user_id=user_id, ip=ip, detail=detail, is_sample=is_sample)
    db.add(e)
    db.flush()
    return e


def _recent(db: Session, etype: str, minutes: int) -> list[SecurityEvent]:
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=minutes)
    return db.query(SecurityEvent).filter(
        SecurityEvent.type == etype, SecurityEvent.created_at >= since).all()


def _dedupe(db: Session, rule: str, detail: str) -> bool:
    """WHY: True if open alert already exists -> skip duplicate."""
    return db.query(Alert).filter_by(rule=rule, detail=detail, status="New").first() is not None


def run_rules(db: Session) -> list[Alert]:
    """3 rules: brute-force, new-IP, perm-denial flood. Returns NEW alerts only."""
    created: list[Alert] = []

    # R1: 5 failed_logins same IP in 5 min -> High.
    fails = _recent(db, "failed_login", 5)
    by_ip: dict[str, int] = defaultdict(int)
    for e in fails:
        by_ip[e.ip] += 1
    for ip, n in by_ip.items():
        if n >= 5:
            detail = f"{n} failed logins from {ip} in 5 min"
            if not _dedupe(db, "brute-force", detail):
                created.append(Alert(rule="brute-force", severity="High", status="New", detail=detail))

    # R2: login_success from IP never seen for that user before -> Medium.
    # WHY: first-seen IP may be credential sharing/theft.
    successes = db.query(SecurityEvent).filter_by(type="login_success").order_by(SecurityEvent.id).all()
    seen: dict[int, set[str]] = defaultdict(set)
    for e in successes:
        if e.user_id is None:
            continue
        if e.ip not in seen[e.user_id] and seen[e.user_id]:
            detail = f"new IP {e.ip} for user {e.user_id}"
            if not _dedupe(db, "new-ip", detail):
                created.append(Alert(rule="new-ip", severity="Medium", status="New", detail=detail))
        seen[e.user_id].add(e.ip)

    # R3: >=10 perm_denied in 10 min (any) -> Medium.
    denied = _recent(db, "perm_denied", 10)
    if len(denied) >= 10:
        detail = f"{len(denied)} permission denials in 10 min (possible probing)"
        if not _dedupe(db, "perm-probe", detail):
            created.append(Alert(rule="perm-probe", severity="Medium", status="New", detail=detail))

    for a in created:
        db.add(a)
    db.commit()
    return created
