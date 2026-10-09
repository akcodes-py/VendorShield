"""App entry. WHY: strict CORS + security headers + versioned routers."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes import approvals, assessments, auth, continuity, documents, frameworks, incidents, itgc, monitoring, policies, reports, risks, users, vendors

app = FastAPI(title="VendorShield - TPRM mini-platform")

# WHY: strict CORS - frontend dev only, never "*".
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    # WHY: output hardening - blocks clickjacking/MIME-sniff.
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "no-referrer"
    return resp


app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(approvals.router, prefix="/api/v1")
app.include_router(vendors.router, prefix="/api/v1")
app.include_router(assessments.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(risks.router, prefix="/api/v1")
app.include_router(policies.router, prefix="/api/v1")
app.include_router(frameworks.router, prefix="/api/v1")
app.include_router(continuity.router, prefix="/api/v1")
app.include_router(itgc.router, prefix="/api/v1")
app.include_router(monitoring.router, prefix="/api/v1")
app.include_router(incidents.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok", "phase": 9}
