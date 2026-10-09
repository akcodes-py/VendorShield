"""Seed SAMPLE data only. WHY: reproducible demo; every row is clearly fake.
Run: python -m app.db.seed  (uses DATABASE_URL from .env)
Tests use SQLite memory instead - see tests/test_phase1.py.
"""
import bcrypt
from datetime import date, timedelta

from app.db.base import Base
from app.db.session import make_engine
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.vendor import Vendor
from app.models.assessment import Question, Assessment, Answer
from app.models.document import Document
from app.models.risk import Risk, Remediation
from app.models.policy import Policy, FrameworkControl
from app.models.monitoring import SecurityEvent, Alert, Incident
from app.models.continuity import Continuity
from app.models.itgc import ITGCCheck
from app.models.audit_log import AuditLog

# WHY: bcrypt with salt - never store plain passwords, even samples.
def pw(plain: str = "Password123!") -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


QUESTIONS_25 = [
    # (domain, text, weight)
    ("Access Control", "SAMPLE: MFA enforced for all remote access?", 3.0),
    ("Access Control", "SAMPLE: Quarterly access reviews performed?", 2.5),
    ("Access Control", "SAMPLE: Least privilege enforced on admin accounts?", 3.0),
    ("Encryption", "SAMPLE: Data encrypted at rest with AES-256?", 3.0),
    ("Encryption", "SAMPLE: TLS 1.2+ enforced in transit?", 2.5),
    ("Encryption", "SAMPLE: Key management process documented?", 2.0),
    ("Incident Response", "SAMPLE: IR plan documented and tested yearly?", 3.0),
    ("Incident Response", "SAMPLE: SOC / on-call escalation defined?", 2.0),
    ("Incident Response", "SAMPLE: Breach notification process within 72h?", 2.5),
    ("Business Continuity", "SAMPLE: BCP/DR plan exists with RTO/RPO?", 3.0),
    ("Business Continuity", "SAMPLE: Backups tested for restore?", 2.5),
    ("Business Continuity", "SAMPLE: Exit / fallback plan for this service?", 2.0),
    ("Compliance", "SAMPLE: Valid ISO 27001 certificate?", 2.5),
    ("Compliance", "SAMPLE: SOC 2 Type II report available?", 2.5),
    ("Compliance", "SAMPLE: Penetration test in last 12 months?", 2.0),
    ("Compliance", "SAMPLE: Data processing agreement signed?", 2.0),
    ("HR Security", "SAMPLE: Background checks for staff with data access?", 1.5),
    ("HR Security", "SAMPLE: Security awareness training yearly?", 1.5),
    ("HR Security", "SAMPLE: Joiner/mover/leaver process defined?", 1.5),
    ("Network Security", "SAMPLE: Firewall + IDS/IPS in place?", 2.5),
    ("Network Security", "SAMPLE: Vulnerability scanning quarterly?", 2.0),
    ("Network Security", "SAMPLE: Network segmentation for client data?", 2.0),
    ("Data Privacy", "SAMPLE: Data retention policy enforced?", 2.0),
    ("Data Privacy", "SAMPLE: DPO / privacy contact designated?", 1.5),
    ("Data Privacy", "SAMPLE: DSAR handling process defined?", 1.5),
]


def run(url: str | None = None):
    engine = make_engine(url)
    Base.metadata.create_all(engine)  # Phase 1 simple; Alembic used for changes later
    db = Session(engine)

    # Clean SAMPLE reruns - WHY: idempotent seed for demo.
    for t in [Answer, Assessment, Question, Remediation, Risk, Document,
              SecurityEvent, Alert, Incident, Continuity, ITGCCheck,
              AuditLog, Policy, FrameworkControl, User, Vendor]:
        db.query(t).delete()
    db.commit()

    # --- Users (one per role) ---
    admin = User(email="admin@example.com", password_hash=pw(), role="Admin", mfa_enabled=False)
    reviewer = User(email="reviewer@example.com", password_hash=pw(), role="Reviewer")
    auditor = User(email="auditor@example.com", password_hash=pw(), role="Auditor")
    db.add_all([admin, reviewer, auditor])
    db.flush()  # get ids before vendors

    # --- 12 SAMPLE vendors ---
    vendor_rows = [
        ("Acme Cloud SAMPLE", "Cloud Hosting", "High", 1, "Approved"),
        ("PayWell SAMPLE", "Payroll", "High", 1, "Assessment"),
        ("MediStore SAMPLE", "Healthcare SaaS", "High", 1, "Onboarding"),
        ("LogiTrack SAMPLE", "Logistics", "Moderate", 2, "Approved"),
        ("EduLearn SAMPLE", "EdTech", "Moderate", 2, "Review"),
        ("FinAudit SAMPLE", "Finance", "High", 1, "Assessment"),
        ("ChatDesk SAMPLE", "Support Tool", "Low", 3, "Approved"),
        ("BuildSoft SAMPLE", "Dev Tools", "Low", 3, "Onboarding"),
        ("FoodDeliv SAMPLE", "Delivery", "Moderate", 2, "Rejected"),
        ("TravelGo SAMPLE", "Travel", "Moderate", 2, "Approved"),
        ("InsurePlus SAMPLE", "Insurance", "High", 1, "Review"),
        ("ShopKart SAMPLE", "E-commerce", "Low", 3, "Offboarded"),
    ]
    vendors = []
    for i, (name, svc, access, tier, life) in enumerate(vendor_rows):
        freq = {1: 6, 2: 12, 3: 24}[tier]
        v = Vendor(
            name=name, service_type=svc, data_access=access, tier=tier,
            contact_name=f"Contact {i+1} SAMPLE", contact_email=f"c{i+1}@sample.test",
            lifecycle=life, onboarding_date=date.today() - timedelta(days=90),
            next_review_date=date.today() + timedelta(days=freq * 30),
            freq_months=freq,
        )
        vendors.append(v)
    db.add_all(vendors)
    db.flush()

    # Vendor-role user locked to vendor 1
    db.add(User(email="vendor1@example.com", password_hash=pw(), role="Vendor", vendor_id=vendors[0].id))

    # --- Questions ---
    for domain, text, weight in QUESTIONS_25:
        db.add(Question(domain=domain, text=text, weight=weight))
    db.flush()

    # --- One SAMPLE assessment with mixed answers ---
    asm = Assessment(vendor_id=vendors[0].id, assessor_id=reviewer.id, status="submitted",
                     overall_score=62.5, risk_level="Medium")
    db.add(asm)
    db.flush()
    qs = db.query(Question).all()
    vals = ["Yes", "Partial", "No"]
    for idx, q in enumerate(qs[:10]):
        db.add(Answer(assessment_id=asm.id, question_id=q.id,
                      value=vals[idx % 3], evidence="SAMPLE evidence note"))

    # --- Documents: valid / expiring / expired ---
    today = date.today()
    db.add_all([
        Document(vendor_id=vendors[0].id, doc_type="ISO27001", stored_name="a1b2c3.pdf",
                 original_name="iso.pdf", mime="application/pdf", size_bytes=1234,
                 issue_date=today - timedelta(days=300), expiry_date=today + timedelta(days=65),
                 review_status="Approved", review_notes="SAMPLE valid"),
        Document(vendor_id=vendors[1].id, doc_type="SOC2", stored_name="d4e5f6.pdf",
                 original_name="soc2.pdf", mime="application/pdf", size_bytes=2345,
                 issue_date=today - timedelta(days=340), expiry_date=today + timedelta(days=10),
                 review_status="Pending", review_notes="SAMPLE expiring in 30 days"),
        Document(vendor_id=vendors[2].id, doc_type="Pentest", stored_name="789abc.pdf",
                 original_name="pentest.pdf", mime="application/pdf", size_bytes=3456,
                 issue_date=today - timedelta(days=400), expiry_date=today - timedelta(days=5),
                 review_status="Expired", review_notes="SAMPLE expired"),
    ])

    # --- Risks + remediations ---
    r1 = Risk(vendor_id=vendors[0].id, description="SAMPLE: No MFA on admin console",
              category="cyber", likelihood=4, impact=5, inherent_score=20,
              controls="None", residual_score=20, owner="reviewer@example.com", status="open",
              due_date=today + timedelta(days=14))
    r2 = Risk(vendor_id=vendors[1].id, description="SAMPLE: SOC2 report expired",
              category="compliance", likelihood=3, impact=4, inherent_score=12,
              controls="Follow up", residual_score=8, owner="reviewer@example.com", status="mitigating",
              due_date=today - timedelta(days=2))  # overdue SAMPLE
    db.add_all([r1, r2])
    db.flush()
    db.add(Remediation(risk_id=r1.id, action="SAMPLE: Enforce MFA", owner="vendor",
                       due_date=today + timedelta(days=7), status="open"))

    # --- Policies (3 SAMPLE templates) ---
    for title in ["TPRM Policy SAMPLE", "Access Control Policy SAMPLE", "Incident Response Policy SAMPLE"]:
        db.add(Policy(title=title, version="1.0", owner="Admin", approval_status="Approved",
                      review_date=today + timedelta(days=365), is_sample=1))

    # --- Framework controls ---
    db.add_all([
        FrameworkControl(framework="ISO27001", control_id="A.5.15", title="Access control"),
        FrameworkControl(framework="ISO27001", control_id="A.8.24", title="Cryptography"),
        FrameworkControl(framework="NISTCSF", control_id="PR.AC-1", title="Identities managed"),
    ])

    # --- SOC SAMPLE events ---
    db.add(SecurityEvent(type="failed_login", user_id=reviewer.id, ip="1.2.3.4",
                         detail="SAMPLE: 5 failed logins in 5 min", is_sample=1))
    db.add(Alert(rule="5 failed logins in 5 min", severity="High", status="New",
                 detail="SAMPLE alert for demo"))
    db.add(Incident(title="SAMPLE: Phishing-linked vendor access", vendor_id=vendors[0].id,
                    severity="High", status="Detected"))

    # --- Continuity + ITGC + audit ---
    for v in vendors[:6]:
        db.add(Continuity(vendor_id=v.id, rto_hours=24, rpo_hours=12,
                          plan_available=(v.tier != 1), last_test_date=today - timedelta(days=200),
                          exit_plan=False))
    db.add(ITGCCheck(domain="access", control="SAMPLE: Quarterly access review", evidence="seed", status="Pass"))
    db.add(AuditLog(actor_id=admin.id, action="seed", entity_type="db", entity_id=None,
                    ip="127.0.0.1", diff_json='{"note": "SAMPLE seed loaded"}'))

    db.commit()
    print(f"Seeded SAMPLE: 4 users, {len(vendors)} vendors, {len(QUESTIONS_25)} questions.")
    db.close()


if __name__ == "__main__":
    run()
