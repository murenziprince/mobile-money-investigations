"""reference.py - independent pure-Python answers computed ONLY from the captured CSV files.

Used for (a) the Section 6.1 "independent check against captured CSV rows" and (b) validating both databases.
  python reference.py --all      # compute all 61 reference answers -> results/reference_answers.json
  python reference.py --checks   # print one device overlap and one chain + one cycle verified from CSV rows
One streaming pass over transfers.csv (about a minute); nothing here touches PostgreSQL or Neo4j.
"""
import csv
import json
import os
import sys
from collections import defaultdict, deque
from datetime import date, datetime, timedelta

from config import DATA_DIR, RESULTS_DIR, SETS, cat_str, set_params
from queries import BOUNDS, DEPTHS

REF_FILE = os.path.join(RESULTS_DIR, "reference_answers.json")


def read_csv(name):
    with open(os.path.join(DATA_DIR, f"{name}.csv"), newline="") as f:
        r = csv.reader(f)
        next(r)
        for row in r:
            yield row


def load_small():
    region = {int(c): rg for c, rg in read_csv("customers")}
    acct = {int(a): (int(c), role) for a, c, role in read_csv("accounts")}
    dev_type = {int(d): t for d, t in read_csv("devices")}
    ad = [tuple(int(x) for x in r) for r in read_csv("account_devices")]
    return region, acct, dev_type, ad


def scan_transfers(acct, windows):
    """One pass: daily totals, edges inside any window, and person->person adjacency (for Q7)."""
    lo = min(w[0] for w in windows)
    hi = max(w[1] for w in windows)
    daily = defaultdict(lambda: [0, 0])
    out = defaultdict(list)   # sender -> [(t, id, receiver, amount)] for edges in a window
    adj = defaultdict(set)    # person -> persons
    role = {a: v[1] for a, v in acct.items()}
    is_person = [False] * (max(acct) + 1)
    for a, v in acct.items():
        is_person[a] = v[1] == "person"
    for tid, s, r, t, amt in read_csv("transfers"):
        s = int(s); r = int(r); t = int(t); amt = int(amt)
        d = daily[(t + 7200) // 86400]       # CAT is a fixed UTC+2: no daylight-saving shifts
        d[0] += 1; d[1] += amt
        if is_person[s] and is_person[r]:
            adj[s].add(r)
        if lo <= t < hi:
            for w in windows:
                if w[0] <= t < w[1]:
                    out[s].append((t, int(tid), r, amt))
                    break
    return daily, out, adj


def amount_ok(prev, nxt):
    return 90 * prev <= 100 * nxt <= 105 * prev


def q1(out, p):
    rows = [e for e in out.get(p["account"], []) if p["start"] <= e[0] < p["end"]]
    return [(len(rows), sum(e[3] for e in rows))]


def q5_chains(out, p):
    a = p["account"]
    res = []
    for t1, id1, b, a1 in out.get(a, []):
        if not (p["start"] <= t1 < p["end"]):
            continue
        for t2, id2, c, a2 in out.get(b, []):
            if not (t1 < t2 <= t1 + 600 and amount_ok(a1, a2)):
                continue
            for t3, id3, d, a3 in out.get(c, []):
                if t2 < t3 <= t2 + 600 and amount_ok(a2, a3) and len({a, b, c, d}) == 4:
                    res.append(((id1, id2, id3), d, (t1, t2, t3), (a1, a2, a3), (a, b, c, d)))
    return res


def q6_cycles(out, p):
    a, res = p["account"], []
    def dfs(cur, path):
        first = path[0]
        for t, tid, r, amt in out.get(cur, []):
            last = path[-1]
            if not (t > last[0] and t < p["end"] and t <= first[0] + 1800 and amount_ok(last[3], amt)):
                continue
            np_ = path + [(t, tid, r, amt)]
            if r == a:
                if 3 <= len(np_) <= 8:
                    res.append(np_)
            elif len(np_) < 8:
                dfs(r, np_)
    for t, tid, r, amt in out.get(a, []):
        if p["start"] <= t < p["end"] and r != a:
            dfs(r, [(t, tid, r, amt)])
    return res


def q3(ad, dev_type, p):
    mine = {d: (f, l) for a, d, f, l, _ in ad if a == p["account"]}
    res = []
    for a, d, f, l, _ in ad:
        if a != p["account"] and d in mine:
            s, e = max(f, mine[d][0]), min(l, mine[d][1])
            if s <= e:
                res.append((a, d, dev_type[d], s, e))
    return sorted(res)


def q4(region, acct, ad, p):
    nbr = defaultdict(list)
    for a, (c, _) in acct.items():
        nbr[("A", a)].append(("C", c)); nbr[("C", c)].append(("A", a))
    for a, d, *_ in ad:
        nbr[("A", a)].append(("D", d)); nbr[("D", d)].append(("A", a))
    start = ("A", p["account"])
    dist = {start: 0}
    q = deque([start])
    while q:
        u = q.popleft()
        if dist[u] >= p["depth"]:
            continue
        for v in nbr[u]:
            if v not in dist:
                dist[v] = dist[u] + 1
                q.append(v)
    counts = defaultdict(int)
    for (k, i), dd in dist.items():
        if k == "A" and i != p["account"] and dd <= p["depth"]:
            counts[region[acct[i][0]]] += 1
    return sorted(counts.items())


def q7_length(adj, acct, p):
    s, t, bound = p["account"], p["destination"], p["bound"]
    if acct[s][1] != "person" or acct[t][1] != "person":
        return None
    dist = {s: 0}
    q = deque([s])
    while q:
        u = q.popleft()
        if u == t:
            return dist[u]
        if dist[u] >= bound:
            continue
        for v in adj.get(u, ()):
            if v not in dist:
                dist[v] = dist[u] + 1
                q.append(v)
    return None


def compute_all():
    from queries import build_cases
    region, acct, dev_type, ad = load_small()
    windows = [set_params(k)["start"] for k in SETS]
    wins = [(set_params(k)["start"], set_params(k)["end"] + 1200) for k in SETS]
    daily, out, adj = scan_transfers(acct, wins)
    answers = {}
    for c in build_cases():
        p, q = c["params"], c["q"]
        if q == "Q1": rows = q1(out, p)
        elif q == "Q2":
            rows = [((date(1970, 1, 1) + timedelta(days=k)).isoformat(), n, s)
                    for k, (n, s) in sorted(daily.items())]
        elif q == "Q3": rows = q3(ad, dev_type, p)
        elif q == "Q4": rows = q4(region, acct, ad, p)
        elif q == "Q5": rows = [(c_[0][0], c_[0][1], c_[0][2], c_[1]) for c_ in q5_chains(out, p)]
        elif q == "Q6": rows = [(tuple(e[1] for e in cy), len(cy)) for cy in q6_cycles(out, p)]
        else: rows = [(q7_length(adj, acct, p),)]
        answers[c["id"]] = [list(map(lambda v: list(v) if isinstance(v, tuple) else v, r)) for r in sorted(rows, key=repr)]
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(REF_FILE, "w") as f:
        json.dump(answers, f)
    print(f"wrote {REF_FILE} ({len(answers)} cases)")
    return answers


def load_reference():
    with open(REF_FILE) as f:
        raw = json.load(f)
    def tup(v): return tuple(tup(x) for x in v) if isinstance(v, list) else v
    return {k: sorted((tup(r) for r in v), key=repr) for k, v in raw.items()}


def independent_checks():
    """Printable evidence: one device overlap and one chain + one cycle re-derived from captured CSV rows."""
    region, acct, dev_type, ad = load_small()
    p = set_params("B")
    print("=== Independent check 1: device overlap for set B account", p["account"], "===")
    rows = q3(ad, dev_type, p)
    a_, d_, t_, s_, e_ = rows[0]
    mine = [r for r in ad if r[0] == p["account"] and r[1] == d_][0]
    other = [r for r in ad if r[0] == a_ and r[1] == d_][0]
    print(f"account {p['account']} on device {d_}: days [{mine[2]},{mine[3]}] (CSV account_devices.csv)")
    print(f"account {a_} on device {d_}: days [{other[2]},{other[3]}]")
    print(f"max(first)={max(mine[2], other[2])} <= min(last)={min(mine[3], other[3])} -> overlap [{s_},{e_}], access_type={t_}")
    wins = [(set_params(k)["start"], set_params(k)["end"] + 1200) for k in ("A", "B", "C")]
    _, out, _ = scan_transfers(acct, wins)
    pa = set_params("A")
    ch = q5_chains(out, pa)
    print("\n=== Independent check 2: Q5 chain for set A (from transfers.csv rows) ===")
    for c in ch[:1]:
        ids, final, ts, am, ac = c
        for i in range(3):
            print(f"  transfer {ids[i]}: {ac[i]} -> {ac[i+1]}  {cat_str(ts[i])}  {am[i]:,} RWF")
        print(f"  gaps {ts[1]-ts[0]} s, {ts[2]-ts[1]} s (<=600); ratios {100*am[1]/am[0]:.3f}%, {100*am[2]/am[1]:.3f}% (90-105%)")
    print("\n=== Independent check 3: Q6 cycle for set A ===")
    for cy in q6_cycles(out, pa)[:1]:
        for t, tid, r, amt in cy:
            print(f"  transfer {tid}: ... -> {r}  {cat_str(t)}  {amt:,} RWF")
        print(f"  length {len(cy)}, span {cy[-1][0]-cy[0][0]} s (<=1800), returns to account {pa['account']}")


if __name__ == "__main__":
    if "--checks" in sys.argv:
        independent_checks()
    else:
        compute_all()
