"""run_questions.py - run one question's paired SQL/Cypher results for all review sets (screenshot helper).

  python run_questions.py q1 [--engine pg|neo|both] [--q7 v1|v2]
Prints the query text, then a result table per set and engine, with a MATCH/DIFFER verdict.
"""
import argparse
import time

import db
from config import cat_str
from queries import build_cases, cypher_text, params_for, sql_text


def run_case(engine, case, q7="v1", timeout_s=None):
    if engine == "pg":
        return db.run_pg(sql_text(case, q7), params_for(case), timeout_s)
    return db.run_neo(cypher_text(case), params_for(case), timeout_s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("question", help="q1..q7")
    ap.add_argument("--engine", default="pg", choices=["pg", "neo", "both"])
    ap.add_argument("--q7", default="v1", choices=["v1", "v2"])
    ap.add_argument("--rows", type=int, default=6, help="max rows to print per case")
    a = ap.parse_args()
    q = a.question.upper()
    cases = [c for c in build_cases() if c["q"] == q]
    engines = ["pg", "neo"] if a.engine == "both" else [a.engine]
    print(f"=== {q} | {time.strftime('%Y-%m-%d %H:%M:%S')} local ===")
    for c in cases:
        p = c["params"]
        extra = ""
        if "start" in p:
            extra = f" window {cat_str(p['start'])} .. {cat_str(p['end'])}"
        print(f"\n--- {c['id']} (account={p.get('account')}, destination={p.get('destination')}){extra}")
        results = {}
        for e in engines:
            t0 = time.perf_counter()
            rows = run_case(e, c, a.q7)
            ms = (time.perf_counter() - t0) * 1000
            results[e] = db.canon(c, rows)
            print(f"  [{e:3s}] {len(rows)} row(s) in {ms:,.1f} ms")
            for r in results[e][: a.rows]:
                print("        ", r)
            if len(results[e]) > a.rows:
                print(f"         ... {len(results[e]) - a.rows} more rows")
        if len(engines) == 2:
            print("  =>", "MATCH" if results["pg"] == results["neo"] else "DIFFER")
    db.close_all()


if __name__ == "__main__":
    main()
