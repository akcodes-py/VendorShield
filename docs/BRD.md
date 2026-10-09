# BRD - VendorShield (Third-Party Risk Management mini-platform)

## 1. Business problem
Consulting clients outsource to cloud, payroll, SaaS vendors but track risk in spreadsheets:
no single vendor lifecycle, no scored assessments, expired ISO/SOC2 certs go unnoticed,
risks lack owners/dates, auditor evidence is scattered. A vendor incident becomes a client incident.

## 2. Objectives
- Single register of vendors with tier-based review cadence.
- Scored 25-question security assessments with failed-control remediations.
- Document review with expiring/expired flags.
- Risk register (5x5), remediations, exception approvals.
- GRC workflow: Reviewer assesses -> Admin approves; privileged actions need 2nd Admin.
- Audit-ready: immutable audit log, ITGC checklist, coverage vs ISO 27001 / NIST CSF.
- SOC basics: events, 3 detection rules, alerts, stepwise incidents.
- Reporting: dashboard, vendor + executive PDFs, pandas analysis.

## 3. Stakeholders
Admin (owns platform), Reviewer (assesses), Auditor (read-only + evidence),
Vendor contact (answers own questionnaire), senior management (executive PDF).

## 4. Scope (in)
Phases 1-11 as built: vendors, assessments, docs (+AI stub OFF), risks, policies,
frameworks, continuity, ITGC, SOC/incidents, React UI, dashboard/PDFs/analysis, VAPT docs.
Local dev only: PostgreSQL + SQLite tests, no Docker/cloud/CI.

## 5. Out of scope
Prod hosting, TLS/WAF, SSO, real Gemini calls (stub only), mobile app, multi-tenancy.

## 6. Assumptions
- Single analyst runs demo locally; SAMPLE seed data clearly labelled.
- JWT in localStorage is demo-grade (prod: httpOnly cookies).
- Assessments lack `created_at` (trend uses id order; noted in insights).

## 7. Requirements (summary)
- R1: Vendor CRUD + lifecycle allowlist + tier freq (6/12/24mo).
- R2: 25 weighted Qs, evidence for No/Partial, weighted score + levels.
- R3: Secure upload (allowlist, header check, 10MB, random names) + expiry flags.
- R4: Risks LxI 1-5, residual<=inherent with controls proof, heatmap, overdue flags.
- R5: Policies + versions, framework coverage %, BCP gaps, ITGC Pass-needs-evidence.
- R6: RBAC + MFA (Admin) + SoD + audit + rate limits + security headers.
- R7: 3 detection rules + triage + stepwise incidents + SAMPLE simulator.
- R8: Role-based React UI for all modules.
- R9: Dashboard, 2 PDFs, pandas charts + insights.
- R10: 61 pytest tests, Bandit clean, VAPT + SECURITY docs.
