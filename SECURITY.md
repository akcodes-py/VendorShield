# Security Policy - VendorShield

Report issues locally (portfolio project, no hosted prod). Do not test systems you do not own.

## OWASP Top 10 (2021) mapping - what is implemented

| Risk | Implemented |
|------|-------------|
| A01 Broken Access Control | `require_roles` on every endpoint; Vendor scoped by `vendor_id` (IDOR 403s); Auditor read-only; SoD (2nd Admin for role/vendor-delete/exception); tested in `test_rbac_attack`, `test_vendors`, `test_documents`, `test_risks`, `test_monitoring` |
| A02 Cryptographic Failures | bcrypt passwords; JWT short access (15min) + rotating refresh (7d, jti revoke); TOTP MFA for Admin; TLS expected in prod (local demo is HTTP) |
| A03 Injection | Pydantic validation on all inputs; SQLAlchemy ORM only (grep for raw SQL clean); evidence-required rules; SQLi payload test passes |
| A04 Insecure Design | Tier->frequency, lifecycle allowlist, stepwise incident flow, residual<=inherent with controls proof, approval workflows |
| A05 Misconfiguration | `.env` secrets + `.env.example`; strict CORS (`localhost:5173` only); security headers (nosniff/DENY/no-referrer); `backend/uploads` outside public path |
| A06 Vulnerable Components | Bandit clean; PyJWT bumped to 2.15.1; esbuild fixed; braces accepted (dev-only, see VAPT); `requirements.txt` pinned for `pip-audit` |
| A07 Auth Failures | Rate limit 5 fails/5min/IP -> 429; MFA enforced for Admin; refresh rotation; revoked-user block; brute-force SOC rule + High alert |
| A08 Data/Software Integrity | Alembic migrations; audit log append-only (no PUT/DELETE); config-change log; policy version history; PDF from server data only |
| A09 Logging Failures | Audit (who/what/when/IP/old->new) on create/update/delete/login; SOC events (failed_login, suspicious_upload, privilege_change) + 3 detection rules + triage |
| A10 SSRF | No server-side URL fetching from user input; Gemini stub OFF by default (no external calls in tests) |

## Additional controls
- Upload: ext+MIME allowlist, magic-header check, 10MB limit, `secrets.token_hex` names.
- Privacy: AI summaries labelled draft, reviewer must confirm; risks note (hallucination + data privacy).
- Sample data: every seed/simulation row labelled SAMPLE; seed password documented demo-only.
