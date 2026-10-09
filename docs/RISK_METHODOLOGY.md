# Risk Methodology

## Assessment scoring (questionnaire)
- 25 questions, each has `weight` (1.0-3.0; critical controls heavier) and `domain` (8 domains).
- Answer values: `Yes=1.0, Partial=0.5, No=0.0, N/A=excluded` (N/A leaves denominator).
- Domain score: `sum(weight*value)/sum(weights of answered) * 100`, rounded 2dp.
- Overall: same formula across all answered questions.
- Levels: `>=85 Low, 60-84 Medium, 40-59 High, <40 Critical`.
- Evidence rule: `No`/`Partial` require >=3 chars evidence (unauditable answers rejected 422).
- Remediation: every failed domain maps via rules table (e.g. Encryption failed ->
  "Enable AES-256 at rest, TLS 1.2+..."); partial domains get "strengthen" notes.
- Code: `app/services/scoring.py` + `remediation.py` (single source; tests assert 66.67 Medium example).

## Risk register (5x5)
- `inherent = likelihood(1-5) x impact(1-5)` (1-25).
- Severity: `1-4 Low, 5-9 Medium, 10-15 High, 16-25 Critical`.
- `residual` starts = inherent; lowering needs `controls` text and `residual<=inherent` (400 otherwise).
- Heatmap: rows impact 5..1, cols likelihood 1..5, cells count open/mitigating risks.
- Overdue: `due_date < today` and status not closed/accepted.
- Categories: cyber, operational, compliance, financial.

## Tiering (review cadence)
- Tier 1 (critical / High data) = every 6 months; Tier 2 = 12; Tier 3 = 24.
- `next_review_date = onboarding/approval date + freq`; tier change recalculates.
- BCP gaps: critical (tier1 or High access) with no plan / no exit / never tested / test >1yr.

## Worked example
Q1 Yes w3, Q2 No w1, Q3 Partial w2 -> `(3*1 + 1*0 + 2*0.5)/6 = 4/6 = 66.67` -> Medium.
Risk L4xI5=20 Critical; with MFA controls residual 8 Medium.
