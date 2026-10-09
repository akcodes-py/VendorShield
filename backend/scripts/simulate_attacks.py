"""SAMPLE attack simulator - DEMO ONLY, never run against prod.
WHY: feeds SecurityEvent with is_sample=1 so detection rules can be demoed
without touching real audit data. Every row clearly labelled SAMPLE.
Run: python -m scripts.simulate_attacks
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db.session import make_engine
from sqlalchemy.orm import Session
from app.models.user import User
from app.services.detection import log_event, run_rules


def main():
    eng = make_engine()
    with Session(eng) as db:
        reviewer = db.query(User).filter_by(email="reviewer@example.com").first()
        uid = reviewer.id if reviewer else None
        print("SAMPLE ONLY: generating demo attack events (is_sample=1)...")
        # 1. brute force: 5 failed logins same IP
        for _ in range(5):
            log_event(db, "failed_login", uid, "9.9.9.9", "SAMPLE: simulated brute force", 1)
        # 2. new IP success after known IP
        log_event(db, "login_success", uid, "1.1.1.1", "SAMPLE: known office IP", 1)
        log_event(db, "login_success", uid, "8.8.8.8", "SAMPLE: unknown IP", 1)
        # 3. permission probing: 10 denials
        for _ in range(10):
            log_event(db, "perm_denied", uid, "9.9.9.9", "SAMPLE: probing admin endpoint", 1)
        # 4. suspicious upload
        log_event(db, "suspicious_upload", uid, "9.9.9.9", "SAMPLE: evil.exe renamed to cert.pdf", 1)
        db.commit()
        alerts = run_rules(db)
        print(f"SAMPLE ONLY: created {len(alerts)} alerts:")
        for a in alerts:
            print(f" - [{a.severity}] {a.rule}: {a.detail}")


if __name__ == "__main__":
    main()
