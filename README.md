# VendorShield — Enterprise Third-Party Risk Management (TPRM) & GRC Platform

[![Security: Bandit Clean](https://img.shields.io/badge/SAST-Bandit%20Clean-brightgreen.svg)](#security--vapt-report)
[![Tests: 61 Passed](https://img.shields.io/badge/Tests-61%2F61%20Passing-success.svg)](#test-suite--adversarial-validation)
[![OWASP Top 10 Mapped](https://img.shields.io/badge/OWASP-Top%2010%20(2021)%20Covered-blue.svg)](#owasp-top-10-2021-control-mapping)
[![Python: FastAPI](https://img.shields.io/badge/Backend-FastAPI%20%7C%20SQLAlchemy-009688.svg)](https://fastapi.tiangolo.com/)
[![Frontend: React Vite](https://img.shields.io/badge/Frontend-React%2018%20%7C%20TailwindCSS-61DAFB.svg)](https://vitejs.dev/)

> **Authored from the Perspective of a Cyber Security & Technology Risk Analyst**  
> *Repository*: [https://github.com/akcodes-py/VendorShield](https://github.com/akcodes-py/VendorShield)  
> *Classification*: Portfolio Security Demonstration Platform (Local Development Architecture)

---

## Executive Summary & Threat Landscape

Modern cybersecurity incidents—such as the SolarWinds supply chain infiltration, the MOVEit transfer zero-day campaign, and Okta customer support breaches—demonstrate that **an organization's security posture is only as resilient as its weakest third-party vendor**. 

Despite this reality, many mid-market enterprises and consulting clients track third-party risk management (TPRM) and Governance, Risk, and Compliance (GRC) through unversioned, disconnected spreadsheets:
* **Zero Lifecycle Governance**: Vendors onboard without continuous risk review, and offboarding fails to revoke access or trigger contract asset sanitization.
* **Subjective, Unaudited Compliance**: Questionnaires are treated as "checkbox exercises," lacking mandatory evidence requirements, domain-weighted calculations, and actionable remediation workflows.
* **Blind Document Expirations**: Critical ISO/IEC 27001 certifications, SOC 2 Type II reports, and certificates of insurance silently expire unnoticed.
* **Disjointed Risk Registers**: Residual risk scores are manually depressed without cryptographic proof or documented compensating controls.
* **Separation of Duties (SoD) Deficits**: Single administrative users hold unilateral power to delete vendors, accept critical risks, or alter audit trails.

**VendorShield** was engineered to solve this systemic operational risk. It provides an end-to-end, defensively engineered TPRM and GRC mini-platform built with **defense-in-depth principles**, strict **Role-Based Access Control (RBAC)**, an **immutable audit trail**, automated **risk scoring algorithms**, and an integrated **SOC telemetry & detection engine**.

---

## Defensive Architecture & Security Engineering

VendorShield is architected around the principle of **assumed breach** and **least privilege**:

```
                                  [ HTTPS / Client Surface ]
                                               │
                                               ▼
                              ┌────────────────────────────────┐
                              │     React 18 + Vite (SPA)      │
                              │   - 13 Role-Filtered Views     │
                              │   - Strict Form Validation     │
                              │   - Encoded UI Renderings      │
                              └───────────────┬────────────────┘
                                              │ JWT (Bearer) / Multipart
                                              ▼
                              ┌────────────────────────────────┐
                              │       FastAPI Gateway          │
                              │   - Security Headers (HSTS/XFO)│
                              │   - Strict CORS Allowlist      │
                              │   - In-Memory IP Rate Limiter  │
                              └───────────────┬────────────────┘
                                              │
                      ┌───────────────────────┴───────────────────────┐
                      ▼                                               ▼
      ┌───────────────────────────────┐               ┌───────────────────────────────┐
      │  Core Security & Auth Guard   │               │   Application Services        │
      │  - Passlib / Bcrypt Hashing   │               │   - Domain Scoring Engine     │
      │  - Short-lived Access JWT     │               │   - Inherent/Residual Matrix  │
      │  - Rotating Refresh + JTI DB  │               │   - Lifecycle State Machine   │
      │  - RFC 6238 TOTP Admin MFA    │               │   - SOC Event Detection Engine│
      │  - Object-Level Tenant Scoping│               │   - ReportLab PDF Generator   │
      └───────────────┬───────────────┘               └───────────────┬───────────────┘
                      │                                               │
                      ▼                                               ▼
      ┌───────────────────────────────────────────────────────────────────────────────┐
      │                 Data & Storage Layer (ORM Parameterization Only)             │
      │  - PostgreSQL 18 (Local Dev / Demo) | SQLite In-Memory (Pytest Suite)        │
      │  - Alembic Structured Migrations                                              │
      │  - Immutable Append-Only Audit Trail (No UPDATE / DELETE Routes)             │
      │  - Sanitized File Vault: Header Check | 10MB Limit | Random Hex UUIDs         │
      └───────────────────────────────────────────────────────────────────────────────┘
```

### 1. Identity, Credential & Access Management (IAM)
* **Short-Lived Access Tokens (15 Minutes)**: Mitigates replay and exfiltration window.
* **Rotating Refresh Tokens (7 Days) with JTI Blacklisting**: Single-use refresh tokens stored in the database; replaying an old refresh token invalidates downstream sessions.
* **Mandatory Multi-Factor Authentication (MFA)**: Admin roles enforce RFC 6238 TOTP setup and challenge verification before privileged actions are unlocked.
* **Dual-Admin Segregation of Duties (SoD)**: Destructive actions (vendor deletion requests, privileged role changes, risk acceptance exceptions) mandate second-analyst review/approval before execution.
* **Object-Level Tenant Scoping**: Vendor users are cryptographically confined to their designated `vendor_id`. IDOR tampering attempts directly trigger HTTP 403 Forbidden responses.

### 2. Secure File Ingestion Pipeline
* **Multi-Layer Validation**: Uploaded vendor evidence (SOC 2, ISO certs, penetration test reports) must satisfy:
  1. Strict file extension allowlist (`.pdf`, `.png`, `.jpg`, `.jpeg`).
  2. MIME type verification against `UploadFile` headers.
  3. **Magic-Byte Header Validation**: Reads binary headers (`%PDF-`, `\x89PNG\r\n\x1a\n`, `\xff\xd8\xff`) to defeat extension masquerading.
* **Path Traversal & Filename Neutralization**: Filenames are discarded and replaced with cryptographic entropy (`secrets.token_hex(16)`), stored outside the public web root in `backend/uploads/`.
* **Resource Exhaustion Defense**: Strict 10MB file-size ceiling blocks disk-fill Denial-of-Service (DoS).
* **AI Summary Containment**: Optional generative analysis (Gemini) is sandboxed, defaulted to `OFF`, marked as `[DRAFT]`, and strictly requires human reviewer sign-off to mitigate data leakage and hallucination risks.

### 3. Injection Prevention & ORM Sanitization
* All incoming requests pass through Pydantic v2 schemas for strong data validation and sanitization.
* Data access strictly operates via SQLAlchemy ORM (100% parameterization). Raw SQL concatenation, string interpolations, and dynamic queries are completely absent (`grep` tested).

---

## GRC & Risk Assessment Methodology

### A. 25-Point Domain-Weighted Security Assessment
Vendors undergo rigorous evaluation across eight core security domains derived from ISO/IEC 27001:2022 and NIST CSF 2.0:
1. **Access Control & Identity Management** (MFA, RBAC, least privilege)
2. **Data Protection & Cryptography** (AES-256 at rest, TLS 1.2+ in transit)
3. **Network & Infrastructure Security** (Segmentation, firewalls, egress controls)
4. **Vulnerability & Patch Management** (Cadence, remediation SLAs)
5. **Incident Response & Resilience** (Logging, playbook testing, breach notification)
6. **Physical & Environmental Security** (Datacenter controls, clean desk)
7. **Human Resources & Training** (Background screening, annual awareness)
8. **Third-Party & Supply Chain Governance** (Sub-processor controls, NDA)

#### Scoring Algorithm:
$$\text{Score} = \left( \frac{\sum (w_i \cdot v_i)}{\sum w_i \text{ for answered questions}} \right) \times 100$$
Where:
* $v_i = 1.0$ (Yes), $0.5$ (Partial), $0.0$ (No).
* $w_i \in [1.0, 3.0]$ (Weight factor corresponding to control criticality).
* Excluded/NA answers are dynamically removed from the denominator.

**Strict Evidence Enforcement**: Answering `No` or `Partial` strictly requires a minimum of 3 characters of documented rationale or evidence. Unverified compliance attempts are rejected with `HTTP 422 Unprocessable Entity`.

| Calculated Score | Risk Tier | Action Requirement |
| :--- | :--- | :--- |
| **85.0 – 100.0** | **Low Risk** | Eligible for immediate operational approval. |
| **60.0 – 84.9** | **Medium Risk** | Conditional approval; remediation plan required within 60 days. |
| **40.0 – 59.9** | **High Risk** | Escalated to Lead Reviewer; mandatory compensating controls. |
| **< 40.0** | **Critical Risk** | Onboarding rejected; formal risk exception workflow required. |

### B. 5x5 Inherent vs. Residual Risk Matrix
* **Inherent Risk Calculation**: $\text{Likelihood } (1\text{--}5) \times \text{Impact } (1\text{--}5) = [1\text{--}25]$.
* **Residual Integrity Rule**: A residual risk score **cannot be lower than inherent risk** without documented compensating controls and auditable implementation proof. Violations return `HTTP 400 Bad Request`.
* **Dynamic Review Cadence**:
  * **Tier 1 (Critical)**: Recurrent assessment every 6 months.
  * **Tier 2 (High / Operational)**: Recurrent assessment every 12 months.
  * **Tier 3 (Commodity / Low)**: Recurrent assessment every 24 months.

---

## SOC Telemetry & Incident Response

VendorShield includes an embedded Security Operations Center (SOC) module monitoring platform events:

| Detection Rule | Trigger Condition | Severity | Automated Action |
| :--- | :--- | :--- | :--- |
| **BRUTE_FORCE_AUTH** | $\ge 5$ failed login attempts within 5 minutes from same IP | **High** | Event ingestion, rate limit throttle (429), alert creation |
| **ANOMALOUS_GEO_IP** | Login detected from previously unseen IP address | **Medium** | Triage alert generated for reviewer investigation |
| **RAPID_PROBE_SCAN** | $\ge 10$ HTTP 403 / 404 forbidden/not found hits within 1 minute | **High** | Alert escalated to Security Analyst incident queue |

### Stepwise Incident Lifecycle
Incidents adhere to a NIST SP 800-61 Rev. 2 containment lifecycle:
$$\text{Triage} \longrightarrow \text{Investigating} \longrightarrow \text{Contained} \longrightarrow \text{Remediated} \longrightarrow \text{Closed}$$
Every state transition mandates analyst notes and is irreversibly recorded in the immutable audit log.

---

## OWASP Top 10 (2021) Control Mapping

| OWASP Category | Architectural Control & Implementation | Verification Proof |
| :--- | :--- | :--- |
| **A01: Broken Access Control** | Role-based dependency injection (`require_roles`); `vendor_id` object scoping; SoD dual-admin verification. | `tests/test_rbac_attack.py`<br>`tests/test_vendors.py` (IDOR 403s) |
| **A02: Cryptographic Failures** | Passwords hashed using bcrypt; short-lived access JWTs (15m); rotating refresh tokens with DB JTI tracking; TOTP MFA. | `tests/test_auth.py`<br>`test_jwt_tamper_rejected` |
| **A03: Injection** | Strict Pydantic validation models; 100% SQLAlchemy ORM parameterization; zero raw SQL execution. | `test_sql_injection_blocked_by_orm` (`x'; DROP TABLE vendors;--` stored inert) |
| **A04: Insecure Design** | Enforced state machines for vendor onboarding; residual $\le$ inherent rule; SoD approvals; BCP gap detection. | `tests/test_risks.py`<br>`tests/test_governance.py` |
| **A05: Security Misconfiguration** | `.env` separation (`.env.example` committed, `.env` git-ignored); explicit CORS origins (`localhost:5173`); security headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`). | `test_security_headers_present`<br>`backend/app/main.py` |
| **A06: Vulnerable Components** | Pinned dependencies; PyJWT patched to 2.15.1; Bandit static analysis 100% clean; zero vulnerable project-level libraries. | `Bandit SAST (0 issues)`<br>`docs/VAPT_REPORT.md` |
| **A07: Auth & Identification** | IP-based rate limiting (5 failed attempts per 5 minutes); account lockout signaling; single-use token rotation. | `test_rate_limiting_blocks_bruteforce` (429 response verified) |
| **A08: Software & Data Integrity** | Alembic database schema migrations; append-only audit trail; automated ReportLab PDF document compilation. | `tests/test_reports.py`<br>`tests/test_governance.py` |
| **A09: Logging & Monitoring** | Structured audit logging (`who`, `what`, `when`, `ip_address`, `changes_json`); SOC telemetry event table; detection engine. | `tests/test_monitoring.py`<br>`test_audit_trail_immutable` |
| **A10: SSRF** | Zero dynamic external URL ingestion or server-side outbound requests; AI summary engine disabled by default. | Architecture audit (`docs/ARCHITECTURE.md`) |

---

## Test Suite & Adversarial Validation

The application undergoes 61 automated tests including dedicated adversarial simulations:

```bash
cd backend
python -m pytest tests/ -v
```

### Adversarial Test Highlights
* **`test_sql_injection_blocked_by_orm`**: Injects raw SQL payloads (`x'; DROP TABLE vendors;--`) into vendor attributes; confirms inert persistence with schema integrity preserved.
* **`test_malicious_uploads_blocked`**: Probes file upload with `.exe` extensions, MIME header tampering, empty payloads, and files exceeding 10MB limits.
* **`test_path_traversal_filename_neutralised`**: Tests directory traversal strings (`../../../../etc/passwd`) in file upload metadata; verifies filenames are purged and replaced with 32-character hex hashes.
* **`test_jwt_tamper_rejected`**: Validates signature manipulation, token expiration boundaries, and refresh-token-as-access-token type confusion attacks (all return HTTP 401).
* **`test_vendor_idor_blocked`**: Validates that authenticated vendor users receive HTTP 403 when requesting assessments, documents, or risks belonging to other vendors.
* **`test_xss_payload_stored_not_executed`**: Injects `<script>alert('XSS')</script>` in input fields; verifies that React default output escaping and ReportLab XML-escaped Flowables prevent DOM execution.

---

## Platform Role Hierarchy & Credentials

The database seeds four discrete operational roles for local testing:

| Role | Username / Email | Password | Access Privileges |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@example.com` | `Password123!` | System configuration, user provisioning, TOTP MFA, 2nd-Admin approvals, full audit logs. |
| **Reviewer** | `reviewer@example.com` | `Password123!` | Vendor assessments, document reviews, risk register management, incident triage. |
| **Auditor** | `auditor@example.com` | `Password123!` | Read-only compliance inspection, ITGC checklist, exportable audit reports. |
| **Vendor Contact** | `vendor1@example.com` | `Password123!` | Scoped access: view assigned questionnaires and upload compliance evidence. |

*(All seed credentials represent local demonstration data only and are explicitly tagged `[SAMPLE]` in the persistent store).*

---

## Quickstart & Local Setup Guide

### Prerequisites
* **Python**: 3.10+ (tested on Python 3.12 / 3.13)
* **Node.js**: 18+ & npm
* **PostgreSQL**: 15+ (Local instance on port 5432)

### Step 1: Clone Repository
```bash
git clone https://github.com/akcodes-py/VendorShield.git
cd VendorShield
```

### Step 2: Backend Configuration & Service Launch
```bash
cd backend

# Create local environment file
copy .env.example .env

# Install backend dependencies
pip install -r requirements.txt

# Create PostgreSQL database (Windows PowerShell)
& "C:\Program Files\PostgreSQL\18\bin\createdb.exe" -U postgres -h localhost vendorshield

# Seed database with sample vendors, controls, and users
python -m app.db.seed

# Run the full automated security and functional test suite (61 tests)
python -m pytest tests/ -q

# Start FastAPI backend server (:8000)
uvicorn app.main:app --reload
```

### Step 3: Frontend Web Client Launch
Open a second terminal window:
```bash
cd frontend

# Install node dependencies
npm install --legacy-peer-deps

# Start Vite development server (:5173)
npm run dev
```

Navigate your browser to `http://localhost:5173` and log in with any of the demo credentials above.

---

## Project Structure

```
VendorShield/
├── .gitignore                   # Comprehensive git exclusions (secrets, uploads, build artifacts)
├── SECURITY.md                  # Coordinated vulnerability disclosure policy & security controls
├── MANUAL.pdf                   # Operational user & analyst system manual
├── README.md                    # Core documentation written by Cybersecurity Analyst
├── backend/
│   ├── alembic/                 # Database schema migrations
│   ├── app/
│   │   ├── api/v1/routes/       # 13 REST API route controllers (RBAC enforced)
│   │   ├── core/                # JWT auth, audit logging, rate limiting, security configs
│   │   ├── db/                  # Session management & deterministic seed scripts
│   │   ├── models/              # SQLAlchemy relational models
│   │   ├── schemas/             # Pydantic v2 validation models
│   │   ├── services/            # Scoring, remediation rules, SOC detection, ReportLab PDFs
│   │   └── main.py              # Application factory with CORS & security middleware
│   ├── reports/                 # Offline pandas/Matplotlib analytics & insights
│   ├── scripts/                 # Attack simulator, manual builder, cert expiry monitor
│   ├── tests/                   # 61 pytest functional and adversarial security tests
│   └── uploads/                 # Quarantined non-public evidence vault (.gitkeep tracked)
├── frontend/
│   ├── src/
│   │   ├── components/          # Reusable UI components & navigation layouts
│   │   ├── context/             # AuthContext with JWT lifecycle state
│   │   ├── pages/               # 13 Role-filtered views (Dashboard, Vendors, Risks, SOC, etc.)
│   │   └── services/            # Axios API client with automatic bearer injection
│   └── vite.config.js           # Vite development server configuration
├── docs/                        # Formal security and architecture documentation
│   ├── ARCHITECTURE.md          # Data flow & defensive architecture diagrams
│   ├── BRD.md                   # Business requirements & operational problem definition
│   ├── INTERVIEW_GUIDE.md       # Analyst talking points & behavioral interview prep
│   ├── PRESENTATION_OUTLINE.md  # 10-minute executive presentation deck guide
│   ├── RISK_METHODOLOGY.md      # Detailed 5x5 matrix & domain scoring equations
│   ├── USER_STORIES.md          # Persona acceptance criteria
│   └── VAPT_REPORT.md           # Full vulnerability assessment & pentest audit report
└── postman/
    └── VendorShield.postman_collection.json  # Complete API testing collection
```

---

## Analyst Threat Model & Limitations

In the spirit of transparent security engineering, the following architectural decisions and known constraints are documented:

1. **Token Storage**: The current demonstration client stores JWT access tokens in browser `localStorage`. In an enterprise production deployment, tokens should be transitioned to hardened `HttpOnly`, `Secure`, `SameSite=Strict` session cookies to eliminate XSS-based exfiltration vectors.
2. **TLS Termination**: The local development server executes over HTTP (`localhost`). Enterprise deployment requires edge TLS termination (TLS 1.3) via reverse proxy (Nginx / Cloudflare) with automated HSTS preloading.
3. **External AI Isolation**: The Gemini-based summarization capability remains intentionally stubbed and disabled by default to prevent inadvertent transmission of confidential third-party audit reports to external LLM providers.
4. **Audit Immutability**: Platform audit logs are enforced as append-only via application layer constraints (no `PUT` / `DELETE` route exposure). Production implementations should mirror logs to a write-once-read-many (WORM) SIEM (e.g., AWS S3 Glacier with Object Lock or Splunk).

---

## License & Attribution

Developed as an advanced cybersecurity demonstration platform by **Atul Kumar** ([@akcodes-py](https://github.com/akcodes-py)).  
Provided under the MIT License for educational and demonstration purposes.
