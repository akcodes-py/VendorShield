"""List docs expiring in 30 days or expired. WHY: scheduled check for dashboard.
Run: python -m scripts.check_expiry
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy.orm import Session
from app.db.session import make_engine
from app.models.document import Document
from app.services.documents import expiry_flag


def expiring(db: Session):
    for d in db.query(Document).all():
        flag = expiry_flag(d.expiry_date)
        if flag == "Expired":
            print(f"EXPIRED: doc {d.id} vendor {d.vendor_id} expired {d.expiry_date}")
        elif flag == "Expiring":
            print(f"EXPIRING: doc {d.id} vendor {d.vendor_id} expires {d.expiry_date}")


if __name__ == "__main__":
    from sqlalchemy.orm import Session as S
    eng = make_engine()
    with S(eng) as db:
        expiring(db)
