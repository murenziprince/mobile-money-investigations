"""graph/verify_neo4j.py - Section 3.2 step 4: counts, roles, one owner per account, unique transfer_id, audit totals.

Run with Neo4j started:  python graph/verify_neo4j.py     (then python prepare_import.py --clean)
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from neo4j import GraphDatabase  # noqa: E402
from config import AUDIT_FILE, NEO4J_DATABASE, NEO4J_PASSWORD, NEO4J_URI, NEO4J_USER  # noqa: E402

ok_all = True


def check(label, got, want):
    global ok_all
    ok = got == want
    ok_all &= ok
    print(f"{'OK      ' if ok else 'MISMATCH'} {label:36s} got={got!s:>18} expected={want!s:>18}")


def main():
    audit = json.load(open(AUDIT_FILE))["transfers"]
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session(database=NEO4J_DATABASE) as s:
        one = lambda q: s.run(q).single()[0]
        for label, n in (("Customer", 228_000), ("Account", 248_000), ("Device", 228_600)):
            check(f"(:{label}) nodes", one(f"MATCH (n:{label}) RETURN count(n)"), n)
        for rel, n in (("OWNS", 248_000), ("USED_DEVICE", 285_600), ("TRANSFER", 20_003_300)):
            check(f"[:{rel}] relationships", one(f"MATCH ()-[r:{rel}]->() RETURN count(r)"), n)
        check("total nodes", one("MATCH (n) RETURN count(n)"), 704_600)
        check("total relationships", one("MATCH ()-[r]->() RETURN count(r)"), 20_536_900)
        roles = {r["role"]: r["n"] for r in s.run("MATCH (a:Account) RETURN a.role AS role, count(*) AS n")}
        for role, n in (("person", 240_000), ("merchant", 6_000), ("agent", 2_000)):
            check(f"accounts role={role}", roles.get(role, 0), n)
        check("accounts without exactly 1 owner",
              one("MATCH (a:Account) OPTIONAL MATCH (c:Customer)-[:OWNS]->(a) WITH a, count(c) AS k WHERE k <> 1 RETURN count(a)"), 0)
        r = s.run("MATCH ()-[t:TRANSFER]->() RETURN count(t) AS n, min(t.occurred_at) AS mn, "
                  "max(t.occurred_at) AS mx, sum(t.amount_rwf) AS total").single()
        check("transfer count (capture audit)", r["n"], audit["transfer_count"])
        check("min occurred_at", r["mn"], audit["min_occurred_at"])
        check("max occurred_at", r["mx"], audit["max_occurred_at"])
        check("sum amount_rwf", r["total"], audit["sum_amount_rwf"])
        try:    # exact uniqueness test; needs heap for 20M ids, so fall back to a range test if it runs out
            d = one("MATCH ()-[t:TRANSFER]->() RETURN count(DISTINCT t.transfer_id)")
            check("distinct transfer_id", d, audit["transfer_count"])
        except Exception as e:
            print("distinct count failed (", type(e).__name__, "): using min/max/count test instead")
            r2 = s.run("MATCH ()-[t:TRANSFER]->() RETURN min(t.transfer_id) AS lo, max(t.transfer_id) AS hi").single()
            check("transfer_id span == count", r2["hi"] - r2["lo"] + 1, audit["transfer_count"])
    driver.close()
    print("\nALL CHECKS PASSED - you may now run: python prepare_import.py --clean" if ok_all else "\nSOME CHECKS FAILED")
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
