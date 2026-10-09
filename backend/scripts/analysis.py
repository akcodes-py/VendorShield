"""Offline analysis with pandas + Matplotlib. WHY: script, not API - for audit packs.
Outputs (SAMPLE data labelled):
  backend/reports/avg_risk_by_service.png
  backend/reports/failed_controls.png
  backend/reports/score_trend.png
  backend/reports/insights.md
Run: python -m scripts.analysis
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import matplotlib
matplotlib.use("Agg")  # WHY: headless - no display needed on server.
import matplotlib.pyplot as plt
import pandas as pd

from app.db.session import make_engine

OUT = os.path.join(os.path.dirname(__file__), "..", "reports")
os.makedirs(OUT, exist_ok=True)


def main(url: str | None = None):
    eng = make_engine(url)
    risks = pd.read_sql("SELECT * FROM risks", eng)
    vendors = pd.read_sql("SELECT * FROM vendors", eng)
    answers = pd.read_sql("SELECT * FROM answers", eng)
    questions = pd.read_sql("SELECT * FROM questions", eng)
    assess = pd.read_sql("SELECT * FROM assessments", eng)

    lines = ["# VendorShield analysis (SAMPLE data)", ""]

    # 1. avg inherent risk by service type
    if not risks.empty and not vendors.empty:
        m = risks.merge(vendors[["id", "service_type"]], left_on="vendor_id", right_on="id", suffixes=("", "_v"))
        g = m.groupby("service_type")["inherent_score"].mean().sort_values()
        plt.figure()
        g.plot(kind="barh")
        plt.xlabel("avg inherent (LxI)")
        plt.tight_layout()
        plt.savefig(os.path.join(OUT, "avg_risk_by_service.png"))
        plt.close()
        lines += ["## Avg risk by service type", g.to_string(), "",
                  f"Highest: {g.idxmax()} ({g.max():.1f}). Focus reviews there.", ""]
    else:
        lines += ["## Avg risk by service type", "no data", ""]

    # 2. most common failed controls (answers == No -> domain)
    if not answers.empty and not questions.empty:
        f = answers[answers["value"] == "No"].merge(questions, left_on="question_id", right_on="id")
        top = f["domain"].value_counts().head(8)
        plt.figure()
        top.plot(kind="bar")
        plt.ylabel("No count")
        plt.tight_layout()
        plt.savefig(os.path.join(OUT, "failed_controls.png"))
        plt.close()
        lines += ["## Most failed control domains", top.to_string(), "",
                  "Fix top domain first - cheapest risk reduction.", ""]
    else:
        lines += ["## Most failed control domains", "no answers yet", ""]

    # 3. score trend (id order proxy - assessments lack timestamp; honest note)
    if not assess.empty:
        s = assess.sort_values("id")["overall_score"]
        plt.figure()
        plt.plot(s.values, marker="o")
        plt.ylabel("overall score")
        plt.xlabel("assessment order (id; no timestamp stored - see note)")
        plt.tight_layout()
        plt.savefig(os.path.join(OUT, "score_trend.png"))
        plt.close()
        lines += ["## Score trend", f"n={len(s)}, mean={s.mean():.1f}, last={s.iloc[-1]:.1f}", "",
                  "NOTE: assessments have no created_at; x-axis is id order. Add timestamp for real trend.", ""]
    else:
        lines += ["## Score trend", "no assessments yet", ""]

    with open(os.path.join(OUT, "insights.md"), "w") as fh:
        fh.write("\n".join(lines))
    print("Wrote reports/avg_risk_by_service.png, failed_controls.png, score_trend.png, insights.md")


if __name__ == "__main__":
    main()
