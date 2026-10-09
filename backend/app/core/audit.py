"""Audit helper. WHY: every state change must leave who/when/IP/old->new."""
import json

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def write_audit(db: Session, actor_id: int | None, action: str,
                entity_type: str = "", entity_id: int | None = None,
                ip: str = "", diff: dict | None = None):
    # WHY: append-only - no update/delete API exists for audit_logs.
    db.add(AuditLog(
        actor_id=actor_id, action=action, entity_type=entity_type,
        entity_id=entity_id, ip=ip, diff_json=json.dumps(diff or {}),
    ))
