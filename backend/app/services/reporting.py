"""Reporting aggregates + PDFs. WHY: one place so dashboard/API/PDF agree."""
from collections import Counter
from datetime import date
from io import BytesIO

from sqlalchemy.orm import Session

from app.models.assessment import Assessment
from app.models.document import Document
from app.models.risk import Remediation, Risk
from app.models.vendor import Vendor
from app.services.documents import expiry_flag
from app.services.risks import heatmap as _heatmap, severity


def _latest_assessment(db: Session, vendor_id: int) -> Assessment | None:
    return (db.query(Assessment).filter_by(vendor_id=vendor_id, status="submitted")
            .order_by(Assessment.id.desc()).first())


def dashboard_data(db: Session, scope_vendor: int | None = None) -> dict:
    vendors = db.query(Vendor).all()
    if scope_vendor:
        vendors = [v for v in vendors if v.id == scope_vendor]
    vids = {v.id for v in vendors}

    risks = db.query(Risk).filter(Risk.status.in_(["open", "mitigating"])).all()
    risks = [r for r in risks if r.vendor_id in vids]

    docs = db.query(Document).all()
    docs = [d for d in docs if d.vendor_id in vids]

    # vendors by lifecycle + risk level (latest submitted or Unassessed)
    by_life = dict(Counter(v.lifecycle for v in vendors))
    by_level: dict[str, int] = Counter()
    for v in vendors:
        a = _latest_assessment(db, v.id)
        by_level[a.risk_level if a else "Unassessed"] += 1

    open_by_sev = dict(Counter(severity(r.inherent_score) for r in risks))
    hm = _heatmap(dict(Counter((r.likelihood, r.impact) for r in risks)))

    expiring = [{"id": d.id, "vendor_id": d.vendor_id, "expiry": str(d.expiry_date)}
                for d in docs if expiry_flag(d.expiry_date) in ("Expiring", "Expired")]

    overdue_rem = []
    for m in db.query(Remediation).all():
        r = db.get(Risk, m.risk_id)
        if not r or r.vendor_id not in vids:
            continue
        if m.due_date and m.due_date < date.today() and m.status != "done":
            overdue_rem.append({"id": m.id, "risk_id": m.risk_id, "action": m.action[:80],
                                "due": str(m.due_date)})

    # top 5 by max open inherent
    by_vendor: dict[int, list[int]] = {}
    for r in risks:
        by_vendor.setdefault(r.vendor_id, []).append(r.inherent_score)
    top = sorted(((vid, max(s), len(s)) for vid, s in by_vendor.items()),
                 key=lambda x: -x[1])[:5]
    vname = {v.id: v.name for v in vendors}
    top5 = [{"vendor_id": vid, "name": vname.get(vid, "?"), "max_inherent": mx, "open_count": n}
            for vid, mx, n in top]

    total_v = len(vendors) or 1
    assessed = sum(1 for v in vendors if _latest_assessment(db, v.id))
    return {"vendors_by_lifecycle": by_life, "vendors_by_risk_level": dict(by_level),
            "open_risks_by_severity": open_by_sev, "heatmap": hm,
            "expiring_documents": expiring, "overdue_remediations": overdue_rem,
            "top_5_riskiest": top5,
            "assessment_completion_rate": round(assessed / total_v * 100, 1)}


def _pdf(title: str, lines: list[str], tables: list[tuple[str, list[list[str]]]]) -> bytes:
    # WHY: reportlab platypus - simple flowables, no HTML injection risk (Paragraph escaped).
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    story = [Paragraph(title, styles["Title"]), Spacer(1, 12)]
    for ln in lines:
        story += [Paragraph(ln, styles["Normal"]), Spacer(1, 6)]
    for ttitle, rows in tables:
        story += [Paragraph(ttitle, styles["Heading2"])]
        t = Table([["#", "Detail"]] + [[str(i + 1), r] for i, r in enumerate(rows)] or [["-", "none"]])
        t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey)]))
        story += [t, Spacer(1, 8)]
    doc.build(story)
    return buf.getvalue()


def vendor_pdf(db: Session, vendor_id: int) -> bytes:
    v = db.get(Vendor, vendor_id)
    a = _latest_assessment(db, vendor_id)
    risks = db.query(Risk).filter_by(vendor_id=vendor_id).all()
    docs = db.query(Document).filter_by(vendor_id=vendor_id).all()
    lines = [f"Vendor: {v.name} ({v.service_type}, Tier {v.tier}, {v.lifecycle})",
             f"Assessment: {(str(a.overall_score) + ' ' + a.risk_level) if a else 'Not assessed yet'}",
             "SAMPLE data - for demo only."]
    tables = [("Open risks", [f"{r.description[:80]} L{r.likelihood}xI{r.impact}={r.inherent_score} {r.status}"
                              for r in risks if r.status in ("open", "mitigating")]),
              ("Documents", [f"{d.doc_type} {d.expiry_date} flag={expiry_flag(d.expiry_date)} {d.review_status}"
                             for d in docs])]
    return _pdf(f"Vendor Risk Report - {v.name}", lines, tables)


def executive_pdf(db: Session) -> bytes:
    d = dashboard_data(db)
    # WHY: plain language for senior management - no jargon.
    lines = [
        "Executive summary (plain language, SAMPLE data).",
        f"We track {sum(d['vendors_by_lifecycle'].values())} vendors. "
        f"{d['open_risks_by_severity'].get('Critical', 0)} critical open risks need attention first.",
        f"Assessment completion is {d['assessment_completion_rate']}%. "
        f"{len(d['expiring_documents'])} documents are expiring or expired - renew certificates.",
        f"{len(d['overdue_remediations'])} fixes are overdue - chase owners this week.",
        "Recommendation: fix Critical risks, renew expiring ISO/SOC2, test continuity for Tier-1 vendors.",
    ]
    tables = [("Top riskiest vendors",
               [f"{t['name']} max score {t['max_inherent']} ({t['open_count']} open)" for t in d["top_5_riskiest"]])]
    return _pdf("Executive Summary - Third-Party Risk", lines, tables)
