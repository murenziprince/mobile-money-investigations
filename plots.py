"""plots.py - evidence charts and summaries for Q2, Q4 and Section 7.2.

  python plots.py q2 [--engine pg|neo]       # 30-day table, reconciliation with capture totals, results/q2_daily.png
  python plots.py q4 [--engine pg|neo]       # all 24 depth comparisons, count-vs-depth plot, one supporting path
  python plots.py scaling                    # throughput and p95 vs clients -> results/scaling.png (needs load_medians.csv)
"""
import argparse
import csv
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import db  # noqa: E402
from config import AUDIT_FILE, RESULTS_DIR, SETS  # noqa: E402
from queries import DEPTHS, build_cases, cypher_text, params_for, read_query, sql_text  # noqa: E402

COLORS = {"pg": "#1f6feb", "neo": "#d9480f"}
LABELS = {"pg": "PostgreSQL", "neo": "Neo4j"}


def run(engine, case, q7="v1"):
    if engine == "pg":
        return db.run_pg(sql_text(case, q7), params_for(case))
    return db.run_neo(cypher_text(case), params_for(case))


def q2(engine):
    case = [c for c in build_cases() if c["q"] == "Q2"][0]
    rows = db.canon(case, run(engine, case))
    audit = json.load(open(AUDIT_FILE))["transfers"]
    n, total = sum(r[1] for r in rows), sum(r[2] for r in rows)
    print(f"{'date':12s} {'transfers':>12s} {'total RWF':>18s}")
    for d, c, s in rows:
        print(f"{d:12s} {c:12,d} {s:18,d}")
    print(f"\ndays returned: {len(rows)} (expected 30): {'OK' if len(rows) == 30 else 'MISMATCH'}")
    print(f"sum of counts {n:,} vs capture {audit['transfer_count']:,}: {'OK' if n == audit['transfer_count'] else 'MISMATCH'}")
    print(f"sum of RWF    {total:,} vs capture {audit['sum_amount_rwf']:,}: {'OK' if total == audit['sum_amount_rwf'] else 'MISMATCH'}")
    days = [r[0][8:] for r in rows]
    fig, ax = plt.subplots(2, 1, figsize=(10, 6.5), sharex=True)
    ax[0].bar(days, [r[1] / 1e3 for r in rows], color=COLORS[engine])
    ax[0].set_ylabel("transfers per day (thousands)")
    ax[1].bar(days, [r[2] / 1e9 for r in rows], color="#2f9e44")
    ax[1].set_ylabel("value per day (billion RWF)")
    ax[1].set_xlabel("September 2026 (CAT day of month)")
    fig.suptitle(f"Q2 daily transfer activity ({LABELS[engine]})")
    fig.tight_layout()
    out = os.path.join(RESULTS_DIR, "q2_daily.png")
    fig.savefig(out, dpi=140)
    print("saved", out)


def q4(engine):
    cases = [c for c in build_cases() if c["q"] == "Q4"]
    print(f"{'case':10s} {'total':>6s}  regions (sorted)")
    totals = {s: {} for s in SETS}
    for c in cases:
        rows = db.canon(c, run(engine, c))
        t = sum(r[1] for r in rows)
        totals[c["set"]][c["params"]["depth"]] = t
        print(f"{c['id']:10s} {t:6d}  " + ", ".join(f"{r[0]}={r[1]}" for r in rows))
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    for s in SETS:
        ax.plot(DEPTHS, [totals[s][d] for d in DEPTHS], marker="o", label=f"Set {s} (acct {SETS[s]['account']})")
    ax.set_xlabel("maximum links (depth)")
    ax.set_ylabel("distinct other accounts reached")
    ax.set_xticks(DEPTHS)
    ax.legend(fontsize=8)
    ax.set_title(f"Q4 accounts reached vs depth ({LABELS[engine]})")
    fig.tight_layout()
    out = os.path.join(RESULTS_DIR, "q4_depth.png")
    fig.savefig(out, dpi=140)
    print("saved", out)
    print("\nSupporting path (set B, 6 links):")
    case = dict(id="Q4-B-path", q="Q4", set="B", params=dict(SETS["B"], depth=6))
    if engine == "pg":
        rows = db.run_pg(read_query("q4_path.sql"), params_for(case))
    else:
        rows = db.run_neo(read_query("q4_path.cypher").replace("{depth}", "6"), params_for(case))
    print("  " + "  --  ".join(rows[0][0]) if rows else "  (no path)")


def scaling():
    rows = list(csv.DictReader(open(os.path.join(RESULTS_DIR, "load_medians.csv"))))
    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    for i, w in enumerate(("q4", "q7")):
        for j, (key, label) in enumerate((("throughput_rps", "throughput (correct requests/s)"),
                                          ("p95_ms", "p95 latency (ms)"))):
            ax = axes[i][j]
            for e in ("pg", "neo"):
                pts = sorted((int(r["clients"]), float(r[key])) for r in rows if r["engine"] == e and r["workload"] == w)
                if pts:
                    ax.plot([p[0] for p in pts], [p[1] for p in pts], marker="o", color=COLORS[e], label=LABELS[e])
            ax.set_xticks([1, 4, 8, 16])
            ax.set_xlabel("concurrent clients")
            ax.set_ylabel(label)
            ax.set_title(f"{'Q4 depth 10' if w == 'q4' else 'Q7 length-only bound 6'}")
            ax.legend()
    fig.tight_layout()
    out = os.path.join(RESULTS_DIR, "scaling.png")
    fig.savefig(out, dpi=140)
    print("saved", out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["q2", "q4", "scaling"])
    ap.add_argument("--engine", default="pg", choices=["pg", "neo"])
    a = ap.parse_args()
    {"q2": lambda: q2(a.engine), "q4": lambda: q4(a.engine), "scaling": scaling}[a.what]()
    db.close_all()


if __name__ == "__main__":
    main()
