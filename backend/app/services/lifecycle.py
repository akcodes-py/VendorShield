"""Lifecycle rules. WHY: illegal jumps (Approved->Onboarding) blocked in one place."""
from datetime import date, timedelta

from app.services.scoring import tier_frequency

# Allowed next states per current state.
ALLOWED = {
    "Onboarding": {"Assessment", "Rejected"},
    "Assessment": {"Approved", "Rejected"},
    "Approved": {"Review", "Offboarded"},
    "Review": {"Approved", "Rejected", "Offboarded"},
    "Rejected": {"Onboarding"},
    "Offboarded": set(),  # terminal
}

# Who may move to which target (Vendor never, Auditor never).
REVIEWER_TARGETS = {"Assessment", "Review"}
ADMIN_TARGETS = {"Onboarding", "Assessment", "Approved", "Rejected", "Review", "Offboarded"}


def can_transition(frm: str, to: str, role: str) -> tuple[bool, str]:
    if to not in ALLOWED.get(frm, set()):
        return False, f"Illegal {frm}->{to}"
    if role == "Admin":
        ok = to in ADMIN_TARGETS
    elif role == "Reviewer":
        ok = to in REVIEWER_TARGETS or (frm == "Assessment" and False)
        # WHY: Reviewer assesses, only Admin approves/rejects.
        if to in ("Approved", "Rejected", "Offboarded"):
            return False, "Only Admin can Approve/Reject/Offboard"
        ok = True
    else:
        return False, "Role may not transition vendors"
    return ok, ""


def next_review(onboarding: date | None, tier: int) -> tuple[int, date | None]:
    freq = tier_frequency(tier)
    base = onboarding or date.today()
    return freq, base + timedelta(days=freq * 30)
