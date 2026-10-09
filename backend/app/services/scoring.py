"""Scoring formula. WHY: single function so API + tests + docs all match."""
# Yes=1, Partial=0.5, No=0, N/A=excluded from denominator.

VALUE_MAP = {"Yes": 1.0, "Partial": 0.5, "No": 0.0}


def weighted_score(answers: list[tuple[float, str]]) -> float:
    """answers = [(weight, Yes|Partial|No|NA)]. Returns 0-100."""
    num = 0.0
    den = 0.0
    for weight, value in answers:
        if value == "N/A":
            continue
        num += weight * VALUE_MAP.get(value, 0.0)
        den += weight
    if den == 0:
        return 0.0
    return round(num / den * 100, 2)


def level_for(score: float) -> str:
    if score >= 85:
        return "Low"
    if score >= 60:
        return "Medium"
    if score >= 40:
        return "High"
    return "Critical"


def tier_frequency(tier: int) -> int:
    """WHY: critical vendors reviewed more often."""
    return {1: 6, 2: 12, 3: 24}.get(tier, 24)
