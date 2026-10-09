# Interview Guide (module: what / why / how + Q&A)

## Auth/RBAC/audit (Phase 2)
- What: JWT access+refresh, TOTP MFA, 4 roles, append-only audit, login rate limits.
- Why: least privilege + SoD are the GRC backbone; short tokens limit theft.
- How: `core/security.py` (bcrypt/PyJWT/pyotp), `deps.py` (`require_roles`), `rate_limit.py`, `audit.py`; SoD via approvals table.
- Q: access vs refresh? A: 15min access, 7d refresh with jti rotation; type claim stops confusion.
- Q: same Admin approve own request? A: 403, needs 2nd Admin.

## Vendors/lifecycle (Phase 3)
- What: CRUD + allowlist transitions + tier freq + delete-via-approval.
- Why: illegal jumps and stale reviews are classic findings.
- How: `services/lifecycle.py` (ALLOWED map, role targets), `routes/vendors.py`.
- Q: Reviewer Approve? A: 400/403 - Admin only.

## Assessments (Phase 3)
- What: 25 weighted Qs, evidence rule, weighted score + levels + remediations.
- Why: defensible rating, not vibes.
- How: `services/scoring.py`, `remediation.py`; Vendor answers, Reviewer submits.
- Q: 3/1/2 Yes/No/Partial? A: 66.67 Medium; N/A excluded.

## Documents (Phase 4)
- What: secure upload, expiry flags, review, AI stub OFF.
- Why: expired certs = common audit failure; uploads are top attack surface.
- How: ext/MIME/header checks, 10MB, random names, `expiry_flag()`; AI draft needs confirm.
- Q: renamed exe? A: header check + MIME mismatch block it + `suspicious_upload` event.

## Risks (Phase 5)
- What: LxI 5x5, residual proof, heatmap, overdue, exceptions.
- Why: residual without controls is wishful thinking.
- How: `services/risks.py`; residual<=inherent else 400.
- Q: L4xI5? A: 20 Critical.

## Governance/BCP/ITGC (Phase 6)
- What: policies/versions, coverage %, gaps report, Pass-needs-evidence.
- Why: proves framework alignment + exit readiness.
- How: coverage = mapped/total; gaps = tier1/High + missing/untested/no-exit.
- Q: coverage 1/2? A: 50% + unmapped listed.

## SOC/incidents (Phase 7)
- What: events, 3 rules, triage, stepwise incidents, SAMPLE simulator.
- Why: facts->alerts->incidents is the SOC story.
- How: `services/detection.py` (windows + dedupe); `simulate_attacks.py` (is_sample=1).
- Q: dedupe key? A: rule+detail while New.

## Frontend (Phase 8)
- What: 13 role-filtered pages, JWT wrapper, Recharts.
- Why: UI hiding + server enforcement = defence in depth.
- How: `AuthContext.can()`, `api()` with Authorization, vite proxy.
- Q: only hide UI? A: never - backend re-checks; localStorage XSS noted.

## Reporting (Phase 9)
- What: dashboard JSON, 2 PDFs, pandas charts + insights.
- Why: execs fund what they understand.
- How: `services/reporting.py` (BytesIO PDFs); `scripts/analysis.py`.
- Q: trend x-axis? A: id order; `created_at` missing - honestly noted.

## AppSec (Phase 10)
- What: Bandit clean, PyJWT fix, 61 attack tests, VAPT + SECURITY.
- Why: prove you can hack and fix your own app.
- How: ORM-only, headers, CORS, SoD tests, traversal/XSS/JWT tests.
- Q: braces accepted why? A: tailwind 4 breaking; dev-only local.
