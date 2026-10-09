# VAPT Report - VendorShield (self-test on own app, local only)

Author: B.Tech CSE student (portfolio project). Date: 2026-10-09.
Scope: FastAPI backend (`backend/app`), React frontend (`frontend/src`), local dev only.
Out of scope: production hosting, cloud, third-party APIs (Gemini stub OFF).

## Methodology
1. Static: Bandit (Python), `pip-audit` (deps), `npm audit` (frontend), manual grep for raw SQL / `eval` / `subprocess` / `os.system`.
2. Dynamic (own pytest attacks): SQLi payloads, broken access control, IDOR, brute-force, malicious uploads, JWT tamper/expiry/type-confusion, traversal filenames, XSS storage, oversize files.
3. Retest: full pytest suite after each fix.

## Tool results (recorded, not faked)
- Bandit `python -m bandit -r app scripts`: **No issues identified** (2277 LOC).
- Grep `execute\(|text\(|raw sql|os.system|subprocess|eval\(|pickle`: **no hits** (ORM only).
- `pip-audit` (full env): 44 vulns in 11 packages, almost all in non-project packages (django, DRF, ecdsa, langgraph, pypdf2, python-jose, sqlparse, urllib3, multidict, cryptography). Project action: **PyJWT 2.10.1/2.13.0 -> 2.15.1** (fixes PYSEC-2026-4140..4152, 4144, 4183). Auth suite re-ran green. `pip-audit -r requirements.txt` could not build isolated venv (pandas needs VS build tools) - recorded as limitation.
- `npm audit`: esbuild moderate (GHSA-67mh-4wv8-2f99) **fixed via `npm audit fix`**; braces High (GHSA-vfj7-8cjw-p6xm via tailwind 3.4 chain) **accepted**: fix requires tailwind 4 breaking change; dev-server only, local, no prod. Build re-verified.

## Findings
| ID | Severity | Description | Evidence | Fix | Status |
|----|----------|-------------|----------|-----|--------|
| V-01 | High | PyJWT with known CVEs (2.10.1 pinned, 2.13.0 installed) | pip-audit PYSEC-2026-4140..4152 | Bumped to PyJWT==2.15.1 | Fixed, retested (test_auth 7 passed) |
| V-02 | Medium | esbuild dev-server request forgery (<=0.24.2) | npm audit GHSA-67mh-4wv8-2f99 | `npm audit fix` | Fixed, build passes |
| V-03 | High (accepted) | braces stack-exhaustion via tailwind 3.4 chain | npm audit GHSA-vfj7-8cjw-p6xm | Needs tailwind 4 (breaking); local dev only | Accepted, documented |
| V-04 | Medium | SQL injection via free-text fields (vendor name, answers) | `test_sql_injection_blocked_by_orm`: payload `x'; DROP TABLE vendors;--` stored inert, table intact | ORM only + Pydantic; no raw SQL (grep clean) | Fixed by design, tested |
| V-05 | High | Broken access control: Reviewer->Admin endpoints, Vendor->other vendor data | `test_reviewer_cannot_create_user`, `test_vendor_cannot_list_users`, `test_vendor_idor_blocked` (403s) | `require_roles` + vendor scoping on every route | Fixed by design, tested |
| V-06 | Medium | IDOR on users/vendors/docs/risks/reports | Vendor GET other IDs -> 403 (users, vendors, docs, risks, vendor PDF, continuity) | Ownership checks (`_scope`) | Fixed by design, tested |
| V-07 | Medium | Brute-force login | 5 wrong passwords -> 429; `failed_login` SOC events + rule alert | Rate limit (5/5min/IP) + bcrypt + High alert rule | Fixed by design, tested |
| V-08 | High | Malicious upload (exe, spoofed header, MIME mismatch, empty, oversize, traversal) | `test_malicious_uploads_blocked`, `test_path_traversal_filename_neutralised`, `test_oversize_upload_blocked` | Allowlist + header check + 10MB + random names outside public path + `suspicious_upload` event | Fixed by design, tested |
| V-09 | High | JWT tamper / expiry / refresh-as-access confusion | `test_jwt_tamper_rejected`, `test_expired_token_rejected`, `test_refresh_with_access_token_rejected` (all 401) | Signature verify + exp + `type` claim + rotation/revoke | Fixed by design, tested |
| V-10 | Low | Stored XSS (`<script>` in vendor name) | `test_xss_payload_stored_not_executed`: stored inert; React has no `dangerouslySetInnerHTML`; PDF uses escaped Paragraph | Output encoding (React default + reportlab) + security headers | Fixed by design, tested |
| V-11 | Low | Missing timestamps limited trend/SOC windows | Assessments lack `created_at` (trend uses id order, noted); monitoring got `created_at` + Postgres ALTER | Added `created_at` to SOC tables; assessment timestamp deferred (insights.md notes it) | Partially fixed, documented |

## Retest results
- `tests/test_security_extra.py`: 6 passed. Full suite: **61 passed** (55 + 6).
- `npm run build`: passes. `python -m bandit`: clean. Manual auth flows (login/MFA/refresh/SoD) green.

## Limitations (honest)
- Local demo only; no TLS/WAF/prod hardening tested.
- JWT stored in localStorage (XSS risk noted; prod should use httpOnly cookies).
- `perm_denied` auto-logging is manual/simulation-fed; global 403 middleware deferred.
- Sample seed password (`Password123!`) is intentional demo-only, documented.
