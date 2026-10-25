"""compare.py - Section 6.1: run all 61 cases in both engines and compare exactly.

  python compare.py                       # PostgreSQL vs independent CSV reference (no Neo4j needed)
  python compare.py --engines pg,neo      # also run Neo4j and compare PG vs Neo4j vs reference
  python compare.py --q7 v2               # use the improved SQL for Q7 (Section 6.3 recheck)
Full per-case outputs go to results/comparison_<q7>.json; the status table is what you screenshot.
Q7 lengths are compared separately from the validity of the supporting paths (verify_paths).
"""
import argparse
import json
import os
import time

import db
from config import RESULTS_DIR
from queries import build_cases, cypher_text, params_for, read_query, sql_text
from reference import load_reference

QUESTION_COUNTS = dict(Q1=6, Q2=1, Q3=6, Q4=24, Q5=6, Q6=6, Q7=12)


def run_pg(query, params=None):
    return db.run_pg(query, params)


def run_neo(query, params=None):
    return db.run_neo(query, params)


def run_case(engine, case, q7="v1"):
    if engine == "pg":
        return run_pg(sql_text(case, q7), params_for(case))
    return run_neo(cypher_text(case), params_for(case))


def verify_paths(engine, cases, lengths, q7="v2"):
    """One supporting path per successful Q7 case: ids, direction, roles, event existence and length."""
    out = {}
    for c in cases:
        if c["q"] != "Q7" or lengths[c["id"]] is None:
            continue
        p, want = c["params"], lengths[c["id"]]
        if engine == "pg":
            rows = run_pg(read_query("q7_path.sql"), p)
            accounts, transfers = (list(rows[0][0]) if rows else []), None
        else:
            rows = run_neo(cypher_text(c, path=True), p)
            accounts, transfers = (list(rows[0][0]), list(rows[0][1])) if rows else ([], None)
        ok, notes = bool(accounts), []
        if accounts:
            ok &= accounts[0] == p["account"] and accounts[-1] == p["destination"]
            ok &= len(accounts) - 1 == want
            roles = run_pg("SELECT account_id, role FROM accounts WHERE account_id = ANY(%(ids)s)", {"ids": accounts})
            ok &= all(r == "person" for _, r in roles) and len(roles) == len(set(accounts))
            for i, (u, v) in enumerate(zip(accounts, accounts[1:])):
                ev = run_pg("SELECT transfer_id FROM transfers WHERE sender_id=%(u)s AND receiver_id=%(v)s "
                            "ORDER BY transfer_id LIMIT 1", {"u": u, "v": v})
                if not ev:
                    ok = False; notes.append(f"no transfer {u}->{v}")
                elif transfers and ev and transfers[i] is not None:
                    chk = run_pg("SELECT 1 FROM transfers WHERE transfer_id=%(t)s AND sender_id=%(u)s AND receiver_id=%(v)s",
                                 {"t": transfers[i], "u": u, "v": v})
                    if not chk:
                        ok = False; notes.append(f"transfer {transfers[i]} is not {u}->{v}")
        out[c["id"]] = dict(ok=bool(ok), accounts=accounts, transfers=transfers, notes=notes)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engines", default="pg")
    ap.add_argument("--q7", default="v1", choices=["v1", "v2"])
    ap.add_argument("--brief", action="store_true", help="print only failures and the summaries (one-screen screenshot)")
    a = ap.parse_args()
    engines = a.engines.split(",")
    cases = build_cases()
    ref = load_reference()
    results = {e: {} for e in engines}
    secs = {e: 0.0 for e in engines}
    for c in cases:
        for e in engines:
            t0 = time.perf_counter()
            try:
                results[e][c["id"]] = db.canon(c, run_case(e, c, a.q7))
            except Exception as ex:           # a failure is a failed case, never a silent pass
                results[e][c["id"]] = f"ERROR: {type(ex).__name__}: {str(ex)[:80]}"
            secs[e] += time.perf_counter() - t0
    print(f"{'case':10s} {'rows':>6s}  " + "  ".join(f"{e}=ref" for e in engines) + ("  pg=neo" if len(engines) == 2 else ""))
    bad = 0
    per_q = {q: [0, 0] for q in QUESTION_COUNTS}
    for c in cases:
        want = ref[c["id"]] if c["q"] != "Q7" else (ref[c["id"]] or [(None,)])
        marks = []
        for e in engines:
            marks.append(results[e][c["id"]] == want)
        if len(engines) == 2:
            marks.append(results["pg"][c["id"]] == results["neo"][c["id"]])
        ok = all(marks)
        bad += not ok
        per_q[c["q"]][0] += ok; per_q[c["q"]][1] += 1
        n = len(results[engines[0]][c["id"]]) if isinstance(results[engines[0]][c["id"]], list) else "ERR"
        if not a.brief or not ok:
            print(f"{c['id']:10s} {n!s:>6s}  " + "  ".join(("PASS" if m else "FAIL").ljust(6) for m in marks))
    print("\nper-question:", "  ".join(f"{q}: {v[0]}/{v[1]}" for q, v in per_q.items()))
    print(f"TOTAL: {len(cases) - bad}/{len(cases)} cases agree (expected counts {QUESTION_COUNTS})")
    for e in engines:
        print(f"  {e} total query time {secs[e]:.1f} s (Q7 variant {a.q7 if e == 'pg' else 'native'})")
    # Q7 lengths were compared above; now validate one supporting path per successful case separately.
    lengths = {c["id"]: results[engines[0]][c["id"]][0][0] for c in cases if c["q"] == "Q7"
               and isinstance(results[engines[0]][c["id"]], list)}
    paths = {e: verify_paths(e, cases, lengths) for e in engines}
    for e in engines:
        good = sum(v["ok"] for v in paths[e].values())
        print(f"Q7 supporting paths [{e}]: {good}/{len(paths[e])} valid "
              f"(IDs, direction, person roles, event existence, length)")
        for cid, v in list(paths[e].items())[:3]:
            print(f"   {cid}: accounts {v['accounts']} -> {'OK' if v['ok'] else 'INVALID ' + str(v['notes'])}")
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(os.path.join(RESULTS_DIR, f"comparison_{a.q7}.json"), "w") as f:
        json.dump(dict(results=results, q7_paths=paths, mismatches=bad), f, default=str, indent=1)
    db.close_all()
    raise SystemExit(1 if bad else 0)


if __name__ == "__main__":
    main()
