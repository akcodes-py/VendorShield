"""Upload validation + expiry flags. WHY: one place so API + script + tests agree."""
import secrets
from datetime import date, timedelta
from pathlib import Path

from app.core.config import settings

ALLOWED = {  # ext -> expected mime
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}
MAGIC = {  # WHY: header check blocks renamed .exe (fake pdf).
    ".pdf": b"%PDF",
    ".png": b"\x89PNG",
    ".jpg": b"\xff\xd8\xff",
    ".jpeg": b"\xff\xd8\xff",
}

# Absolute dir: backend/uploads regardless of cwd. WHY: never under frontend public.
UPLOAD_ABS = Path(__file__).resolve().parents[2] / "uploads"
UPLOAD_ABS.mkdir(parents=True, exist_ok=True)


def validate_file(filename: str, content_type: str, data: bytes) -> str:
    """Returns clean ext or raises ValueError. WHY: fail closed on mismatch."""
    ext = Path(filename or "").suffix.lower()
    if ext not in ALLOWED:
        raise ValueError(f"Extension {ext} not allowed (pdf/png/jpg only)")
    if content_type not in ("application/pdf", "image/png", "image/jpeg", "application/octet-stream"):
        raise ValueError(f"MIME {content_type} not allowed")
    # mime must match ext (allow octet-stream only if header matches)
    if content_type != "application/octet-stream" and content_type != ALLOWED[ext]:
        # png/jpg cross ok for jpg/jpeg
        if not (ext in (".jpg", ".jpeg") and content_type == "image/jpeg"):
            raise ValueError("Extension/MIME mismatch")
    limit = settings.MAX_UPLOAD_MB * 1024 * 1024
    if len(data) > limit or len(data) == 0:
        raise ValueError(f"Size must be 1B-{settings.MAX_UPLOAD_MB}MB")
    if not data.startswith(MAGIC[ext]):
        raise ValueError("File header does not match extension (possible spoof)")
    return ext


def save_random(data: bytes, ext: str) -> str:
    name = secrets.token_hex(16) + ext  # WHY: random -> no guessing/traversal
    (UPLOAD_ABS / name).write_bytes(data)
    return name


def expiry_flag(expiry: date | None, today: date | None = None) -> str:
    """WHY: single flag logic for API + dashboard + script."""
    if not expiry:
        return "NoExpiry"
    today = today or date.today()
    if expiry < today:
        return "Expired"
    if expiry <= today + timedelta(days=30):
        return "Expiring"
    return "Valid"
