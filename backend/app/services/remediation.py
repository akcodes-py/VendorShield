"""Remediation rules table. WHY: failed control -> fixed suggestion, auditable."""
# Domain -> suggestion when answer is No (Partial gets softer wording).
RULES = {
    "Access Control": "Enforce MFA + quarterly access reviews + least privilege.",
    "Encryption": "Enable AES-256 at rest, TLS 1.2+ in transit, document key management.",
    "Incident Response": "Publish IR plan, define SOC escalation, test breach notification (72h).",
    "Business Continuity": "Define RTO/RPO, test backups + exit/fallback plan.",
    "Compliance": "Renew ISO/SOC2, complete pentest, sign DPA.",
    "HR Security": "Background checks + yearly awareness + joiner/mover/leaver.",
    "Network Security": "Firewall/IDS, quarterly vuln scans, segment client data.",
    "Data Privacy": "Enforce retention, name DPO, define DSAR process.",
}


def suggestions(failed_domains: set[str], partial_domains: set[str]) -> list[str]:
    out = []
    for d in sorted(failed_domains):
        out.append(f"[{d}] FAILED: {RULES.get(d, 'Remediate control.')}")
    for d in sorted(partial_domains):
        if d not in failed_domains:
            out.append(f"[{d}] PARTIAL: strengthen - {RULES.get(d, '')}")
    return out
