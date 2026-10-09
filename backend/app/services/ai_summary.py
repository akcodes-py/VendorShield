"""Optional AI summary (Gemini). WHY: isolated stub, OFF by default - no data leak.
Risks (show in UI + docs):
- Hallucination: model may invent dates/findings -> reviewer MUST confirm.
- Data privacy: never send secrets/PII to external API; only reviewer-approved text.
Real wiring: set AI_SUMMARY_ENABLED=true + GEMINI_API_KEY, then POST to
generativelanguage.googleapis.com with doc text. Stub below keeps tests offline.
"""
from app.core.config import settings
from app.models.document import Document

RISKS_NOTE = ("AI-assisted draft - reviewer must confirm. "
              "Risks: hallucination (may invent findings) + data privacy (no secrets to external API).")


def draft_for(doc: Document) -> tuple[str, str]:
    """Returns (draft, note). Raises RuntimeError if disabled."""
    if not settings.AI_SUMMARY_ENABLED or not settings.GEMINI_API_KEY:
        raise RuntimeError("AI summary disabled (set AI_SUMMARY_ENABLED=true + GEMINI_API_KEY to enable)")
    # WHY: stub uses metadata only - never uploads file bytes without review.
    draft = (f"AI-assisted draft (SAMPLE stub) for {doc.doc_type} vendor {doc.vendor_id}: "
             f"scope=certificate validity, validity={doc.issue_date}->{doc.expiry_date}, "
             f"exceptions=reviewer to verify, key findings=confirm against original. " + RISKS_NOTE)
    return draft, RISKS_NOTE
