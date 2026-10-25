"""bench.py - Sections 6.2 and 6.3: time 21 fixed cases per engine; collect plans.

  python bench.py --engine pg  --q7 v1          # 21 SQL cases, baseline Q7            -> results/timing_pg_v1.csv
  python bench.py --engine neo                  # 21 Cypher cases                      -> results/timing_neo.csv
  python bench.py --engine pg  --q7 v2 --only Q7  # 6.3: the 4 revised Q7 cases        -> results/timing_pg_v2.csv
  python bench.py --summary                     # median/min/max (ms) + PG/Neo ratio   -> results/timing_summary.csv
  python bench.py --plans --engine pg --q7 v1   # EXPLAIN (ANALYZE, BUFFERS)           -> plans/
  python bench.py --plans --engine neo          # PROFILE                              -> plans/
Run ONE database service at a time. 3 untimed warm-ups (180 s limit) then 5 measured runs (60 s limit).
Timings cover submission through receipt of the final row (perf_counter). Errors/timeouts are stored with
their status and are NEVER counted as completed timings. Answers are compared OUTSIDE the timer.
"""
import argparse
import csv
import json
import os
import statistics
import time
from collections import defaultdict
from time import perf_counter

import db
from config import PLANS_DIR, RESULTS_DIR, cat_str
from queries import build_cases, cypher_text, params_for, sql_text
from reference import load_reference

WARMUPS, RUNS, WARM_TIMEOUT, RUN_TIMEOUT = 3, 5, 180, 60


def selected_cases():
    """The 21 timed cases: Q1/Q3/Q5/Q6 B and E (8), Q2 (1), Q4 B/E x 4 depths (8), Q7 B/E x 2 bounds (4)."""
    keep = []
    for c in build_cases():
        if c["q"] == "Q2" or (c["q"] in ("Q1", "Q3", "Q5", "Q6", "Q4", "Q7") and c["set"] in ("B", "E")):
            keep.append(c)
    assert len(keep) == 21, len(keep)
    return keep


def call(engine, case, q7, timeout):
    if engine == "pg":
        return db.run_pg(sql_text(case, q7), params_for(case), timeout)
    return db.run_neo(cypher_text(case), params_for(case), timeout)


def classify(exc):
    return "timeout" if db.is_timeout(exc) else "error"


def bench(engine, q7, only, out_path):
    ref = load_reference()
    cases = [c for c in selected_cases() if not only or c["q"] == only.upper()]
    os.makedirs(RESULTS_DIR, exist_ok=True)
    fields = ["case", "params", "engine", "variant", "phase", "run", "cat_start_time",
              "duration_ms", "row_count", "status", "correct", "error"]
    with open(out_path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for c in cases:
            params = json.dumps({k: v for k, v in c["params"].items() if k not in ("start", "end")})
            want = ref[c["id"]] if c["q"] != "Q7" else (ref[c["id"]] or [(None,)])
            for phase, n, limit in (("warmup", WARMUPS, WARM_TIMEOUT), ("measured", RUNS, RUN_TIMEOUT)):
                for i in range(1, n + 1):
                    started = cat_str(time.time())
                    rows, status, err = None, "ok", ""
                    t0 = perf_counter()
                    try:
                        rows = call(engine, c, q7, limit)
                    except Exception as ex:
                        status, err = classify(ex), f"{type(ex).__name__}: {str(ex)[:120]}"
                        db.close_all()          # drop a possibly broken connection; reconnect on next call
                    dur = (perf_counter() - t0) * 1000
                    correct = ""
                    if rows is not None and phase == "measured":
                        correct = db.canon(c, rows) == want       # compared AFTER the timer stopped
                    w.writerow(dict(case=c["id"], params=params, engine=engine, variant=q7 if engine == "pg" else "native",
                                    phase=phase, run=i, cat_start_time=started,
                                    duration_ms=round(dur, 3) if status == "ok" else "",
                                    row_count=len(rows) if rows is not None else "", status=status,
                                    correct=correct, error=err))
                    fh.flush()
                    print(f"{c['id']:10s} {phase:8s} {i} {status:7s} {dur:10.1f} ms rows={len(rows) if rows is not None else '-'}",
                          flush=True)
    db.close_all()
    print("saved", out_path)


def summarize():
    data = defaultdict(lambda: defaultdict(list))
    status = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for fn in sorted(os.listdir(RESULTS_DIR)):
        if not (fn.startswith("timing_pg_") or fn.startswith("timing_neo")) or not fn.endswith(".csv") or "summary" in fn:
            continue
        label = fn[len("timing_"):-4]               # pg_v1 | pg_v2 | neo
        with open(os.path.join(RESULTS_DIR, fn)) as f:
            for r in csv.DictReader(f):
                if r["phase"] != "measured":
                    continue
                status[label][r["case"]][r["status"]] += 1
                if r["status"] == "ok" and r["correct"] == "True":      # only correct completed runs are timings
                    data[label][r["case"]].append(float(r["duration_ms"]))
    rows = []
    cases = [c["id"] for c in selected_cases()]
    for cid in cases:
        row = {"case": cid}
        for label in ("pg_v1", "pg_v2", "neo"):
            xs = data[label].get(cid)
            if xs:
                row[f"{label}_median_ms"] = round(statistics.median(xs), 2)
                row[f"{label}_min_ms"], row[f"{label}_max_ms"] = round(min(xs), 2), round(max(xs), 2)
                row[f"{label}_n"] = len(xs)
            elif label in status and cid in status[label]:
                row[f"{label}_median_ms"] = "/".join(f"{k}:{v}" for k, v in status[label][cid].items())
        base = row.get("pg_v1_median_ms")
        if isinstance(base, float) and isinstance(row.get("neo_median_ms"), float):
            row["PG_over_Neo_median_ratio"] = round(base / row["neo_median_ms"], 3)
        if isinstance(row.get("pg_v2_median_ms"), float) and isinstance(row.get("neo_median_ms"), float):
            row["PGv2_over_Neo_median_ratio"] = round(row["pg_v2_median_ms"] / row["neo_median_ms"], 3)
        rows.append(row)
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    out = os.path.join(RESULTS_DIR, "timing_summary.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader(); w.writerows(rows)
    print(f"{'case':10s} " + " ".join(f"{k[:18]:>18s}" for k in keys[1:]))
    for r in rows:
        print(f"{r['case']:10s} " + " ".join(f"{str(r.get(k, '')):>18s}" for k in keys[1:]))
    print("saved", out)


# ---------------------------- plans (outside timing) ----------------------------
def neo_profile_text(profile, indent=0):
    a = profile.get("args", {})
    line = (" " * indent + f"{profile.get('operatorType')}  rows={a.get('Rows')} dbHits={a.get('DbHits')} "
            f"estRows={a.get('EstimatedRows')} details={str(a.get('Details', ''))[:110]}")
    return "\n".join([line] + [neo_profile_text(ch, indent + 2) for ch in profile.get("children", [])])


def plans(engine, q7):
    os.makedirs(PLANS_DIR, exist_ok=True)
    wanted = [c for c in build_cases() if c["id"] in ("Q2", "Q4-B-d10", "Q7-B-b6")]
    for c in wanted:
        if engine == "pg":
            variants = ["v1", "v2"] if c["q"] == "Q7" else [q7]
            for v in variants:
                text = sql_text(c, v)
                rows = db.run_pg("EXPLAIN (ANALYZE, BUFFERS) " + text, params_for(c), 180)
                name = f"pg_{c['id']}{'_' + v if c['q'] == 'Q7' else ''}.txt"
                open(os.path.join(PLANS_DIR, name), "w").write(text + "\n\n" + "\n".join(r[0] for r in rows))
                print("wrote", name)
        else:            
            from neo4j import Query
            name = f"neo_{c['id']}.txt"
            try:
                session = db.neo_session()
                result = session.run(Query("PROFILE " + cypher_text(c), timeout=900), params_for(c))
                list(result)
                summary = result.consume()
                text = neo_profile_text(summary.profile)
            except Exception as ex:
                db.close_all()
                text = f"PROFILE did not complete: {type(ex).__name__}: {str(ex)[:200]}"
            open(os.path.join(PLANS_DIR, name), "w").write(cypher_text(c) + "\n\n" + text)
            print("wrote", name)
    db.close_all()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", choices=["pg", "neo"])
    ap.add_argument("--q7", default="v1", choices=["v1", "v2"])
    ap.add_argument("--only", help="restrict to one question, e.g. Q7")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--plans", action="store_true")
    a = ap.parse_args()
    if a.summary:
        return summarize()
    if not a.engine:
        ap.error("--engine is required")
    if a.plans:
        return plans(a.engine, a.q7)
    label = f"pg_{a.q7}" if a.engine == "pg" else "neo"
    bench(a.engine, a.q7, a.only, os.path.join(RESULTS_DIR, f"timing_{label}.csv"))


if __name__ == "__main__":
    main()
