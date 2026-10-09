"""Risk math. WHY: single scoring so API + heatmap + tests agree."""
from datetime import date


def inherent(likelihood: int, impact: int) -> int:
    return likelihood * impact


def severity(score: int) -> str:
    if score >= 16:
        return "Critical"
    if score >= 10:
        return "High"
    if score >= 5:
        return "Medium"
    return "Low"


def is_overdue(due: date | None, status: str, today: date | None = None) -> bool:
    # WHY: closed/accepted never overdue - work is done.
    if status in ("closed", "accepted") or not due:
        return False
    return due < (today or date.today())


def heatmap(counts: dict[tuple[int, int], int]) -> dict:
    """counts keyed (likelihood, impact). Returns matrix + severity totals."""
    matrix = [[counts.get((l, i), 0) for l in range(1, 6)] for i in range(5, 0, -1)]
    by_sev = {"Low": 0, "Medium": 0, "High": 0, "Critical": 0}
    for (l, i), c in counts.items():
        by_sev[severity(l * i)] += c
    return {"matrix": matrix, "by_severity": by_sev,
            "note": "rows impact 5..1, cols likelihood 1..5, cell = open risk count"}
