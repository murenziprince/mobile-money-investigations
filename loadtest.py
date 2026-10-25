"""loadtest.py - Section 7.1: concurrent analysts (multiprocessing, one persistent connection each, Barrier start).

  python loadtest.py --engine pg  --q7 v2          # full matrix for ONE engine: 2 workloads x 1/4/8/16 clients x 3 reps
  python loadtest.py --engine neo
  python loadtest.py --engine pg --workload q4 --clients 4 --reps 1     # a quick single test
  python loadtest.py --summary                     # medians of the 3 repetitions -> the 16 combination table
Workloads: q4 = Q4 depth 10; q7 = Q7 length-only bound 6. Each client cycles review sets A-B-C.
Each client warms up A-B-C once; at barrier release a common start time is set and the deadline is start+15 s.
Cycles keep starting until the deadline (a started cycle is finished); each request follows the previous at once.
Throughput = correct completions / (time from barrier release to the final cycle finishing).
p95 = sorted successful latencies at position ceil(0.95*n), counting from 1.
Run only ONE database service at a time. Use the SQL Q7 version you SELECTED in Section 6 (--q7).
(For a quick smoke test only, MM_LOAD_SECONDS=4 shortens the 15 s window; never use it for submitted results.)
"""
import argparse
import csv
import math
import multiprocessing as mp
import os
import statistics
import time

from config import RESULTS_DIR, set_params

DEADLINE_S = int(os.environ.get("MM_LOAD_SECONDS", "15"))
TIMEOUT_S = 60
CLIENTS, REPS, WORKLOADS = (1, 4, 8, 16), 3, ("q4", "q7")
SETS_CYCLE = ("A", "B", "C")
REQ_FILE = os.path.join(RESULTS_DIR, "load_requests.csv")
REP_FILE = os.path.join(RESULTS_DIR, "load_reps.csv")


def make_case(workload, label):
    p = set_params(label)
    if workload == "q4":
        p["depth"] = 10
        return dict(id=f"Q4-{label}-d10", q="Q4", set=label, params=p)
    p["bound"] = 6
    return dict(id=f"Q7-{label}-b6", q="Q7", set=label, params=p)


def worker(cid, engine, workload, q7, barrier, start_val, out_q):
    import db
    from queries import cypher_text, params_for, sql_text
    cases = [make_case(workload, s) for s in SETS_CYCLE]

    def run(case):
        if engine == "pg":
            return db.run_pg(sql_text(case, q7), params_for(case), TIMEOUT_S)
        return db.run_neo(cypher_text(case), params_for(case), TIMEOUT_S)

    for c in cases:                                   # one untimed warm-up cycle A-B-C
        try:
            run(c)
        except Exception:
            pass
    barrier.wait()
    with start_val.get_lock():                        # first process released sets the common start time
        if start_val.value == 0.0:
            start_val.value = time.time()
    start = start_val.value
    deadline = start + DEADLINE_S
    log, cycle = [], 0
    while time.time() < deadline:                     # start another cycle only before the deadline
        cycle += 1
        for c in cases:                               # ...but always finish the cycle that has started
            t0 = time.perf_counter()
            status, rows = "ok", None
            try:
                rows = db.canon(c, run(c))
            except Exception as ex:
                status = "timeout" if db.is_timeout(ex) else "error"
            dur = (time.perf_counter() - t0) * 1000
            log.append(dict(client=cid, cycle=cycle, case=c["id"], submit_s=round(time.time() - start - dur / 1000, 4),
                            finish_abs=time.time(), duration_ms=round(dur, 3), status=status, rows=rows))
    db.close_all()
    out_q.put(log)


def run_once(engine, workload, n_clients, q7, ref):
    ctx = mp.get_context("spawn")
    barrier, start_val, out_q = ctx.Barrier(n_clients), ctx.Value("d", 0.0), ctx.Queue()
    procs = [ctx.Process(target=worker, args=(i, engine, workload, q7, barrier, start_val, out_q)) for i in range(n_clients)]
    for p in procs:
        p.start()
    while start_val.value == 0.0:                     # wait for the barrier release
        time.sleep(0.05)
    time.sleep(min(3, DEADLINE_S / 2))
    alive = [p.pid for p in procs if p.is_alive()]
    print(f"    active clients now: {len(alive)}/{n_clients} (pids {alive})", flush=True)
    logs = [out_q.get() for _ in procs]               # drain before join (queue would block on full pipes)
    for p in procs:
        p.join()
    start = start_val.value
    log = [r for l in logs for r in l]

    def expected(case_id):
        want = ref[case_id]
        return want or [(None,)] if case_id.startswith("Q7") else want

    # correctness checked AFTER timing, outside the measured intervals
    for r in log:
        r["correct"] = r["status"] == "ok" and r["rows"] == expected(r["case"])
    good = [r for r in log if r["correct"]]
    elapsed = max(r["finish_abs"] for r in log) - start
    lat = sorted(r["duration_ms"] for r in good)
    n = len(lat)
    summary = dict(engine=engine, workload=workload, clients=n_clients,
                   throughput_rps=round(n / elapsed, 3) if elapsed > 0 else 0,
                   median_ms=round(statistics.median(lat), 2) if lat else "",
                   p95_ms=lat[math.ceil(0.95 * n) - 1] if lat else "",
                   completions=n, errors=sum(r["status"] == "error" for r in log),
                   timeouts=sum(r["status"] == "timeout" for r in log),
                   incorrect=sum(r["status"] == "ok" and not r["correct"] for r in log),
                   elapsed_s=round(elapsed, 3), q7_variant=q7 if engine == "pg" else "native")
    return summary, log


def append_csv(path, rows, fields):
    new = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        if new:
            w.writeheader()
        w.writerows(rows)


def summarize():
    rows = list(csv.DictReader(open(REP_FILE)))
    groups = {}
    for r in rows:
        groups.setdefault((r["engine"], r["workload"], int(r["clients"])), []).append(r)
    out = []
    print(f"{'engine':6s} {'workload':8s} {'clients':>7s} {'thr rps':>9s} {'median ms':>10s} {'p95 ms':>9s} {'err':>4s} {'tmo':>4s} {'bad':>4s} reps")
    for (e, w, c), rs in sorted(groups.items()):
        med = lambda k: statistics.median(float(x[k]) for x in rs if x[k] != "")
        row = dict(engine=e, workload=w, clients=c, throughput_rps=round(med("throughput_rps"), 3),
                   median_ms=round(med("median_ms"), 2), p95_ms=round(med("p95_ms"), 2),
                   errors=sum(int(x["errors"]) for x in rs), timeouts=sum(int(x["timeouts"]) for x in rs),
                   incorrect=sum(int(x["incorrect"]) for x in rs), repetitions=len(rs))
        out.append(row)
        print(f"{e:6s} {w:8s} {c:7d} {row['throughput_rps']:9.2f} {row['median_ms']:10.2f} {row['p95_ms']:9.2f} "
              f"{row['errors']:4d} {row['timeouts']:4d} {row['incorrect']:4d} {len(rs)}")
    with open(os.path.join(RESULTS_DIR, "load_medians.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    print("saved results/load_medians.csv")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", choices=["pg", "neo"])
    ap.add_argument("--workload", choices=WORKLOADS)
    ap.add_argument("--clients", type=int)
    ap.add_argument("--reps", type=int, default=REPS)
    ap.add_argument("--q7", default="v2", choices=["v1", "v2"])
    ap.add_argument("--summary", action="store_true")
    a = ap.parse_args()
    if a.summary:
        return summarize()
    if not a.engine:
        ap.error("--engine is required")
    from reference import load_reference
    ref = load_reference()
    os.makedirs(RESULTS_DIR, exist_ok=True)
    for w in ([a.workload] if a.workload else WORKLOADS):
        for c in ([a.clients] if a.clients else CLIENTS):
            for rep in range(1, a.reps + 1):
                print(f"[{a.engine}] workload={w} clients={c} repetition={rep}", flush=True)
                s, log = run_once(a.engine, w, c, a.q7, ref)
                s["repetition"] = rep
                print("   ", {k: s[k] for k in ("throughput_rps", "median_ms", "p95_ms", "completions", "errors", "timeouts", "incorrect")}, flush=True)
                append_csv(REP_FILE, [s], list(s))
                append_csv(REQ_FILE, [dict(engine=a.engine, workload=w, clients=c, repetition=rep, **{k: r[k] for k in
                           ("client", "cycle", "case", "submit_s", "duration_ms", "status", "correct")}) for r in log],
                           ["engine", "workload", "clients", "repetition", "client", "cycle", "case", "submit_s",
                            "duration_ms", "status", "correct"])


if __name__ == "__main__":
    main()
