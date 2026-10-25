"""check_postgres.py - Section 2.2 verification: counts, roles, transfer audit totals vs capture.py.

Run after load_postgres.py:  python check_postgres.py
"""
import json
import sys

import psycopg

from config import AUDIT_FILE, PG

EXPECTED = dict(customers=228_000, accounts=248_000, devices=228_600,
                account_devices=285_600, transfers=20_003_300)
ROLES = dict(person=240_000, merchant=6_000, agent=2_000)


def line(label, got, want):
    ok = got == want
    print(f"{'OK      ' if ok else 'MISMATCH'} {label:34s} got={got!s:>18} expected={want!s:>18}")
    return ok


def main():
    audit = json.load(open(AUDIT_FILE))["transfers"]
    ok = True
    with psycopg.connect(**PG) as conn, conn.cursor() as cur:
        cur.execute("SHOW timezone")
        print("PostgreSQL time zone:", cur.fetchone()[0])
        for t, n in EXPECTED.items():
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            ok &= line(f"{t} rows", cur.fetchone()[0], n)
        cur.execute("SELECT role, COUNT(*) FROM accounts GROUP BY role")
        got = dict(cur.fetchall())
        for r, n in ROLES.items():
            ok &= line(f"accounts role={r}", got.get(r, 0), n)
        cur.execute("SELECT COUNT(*), MIN(occurred_at), MAX(occurred_at), SUM(amount_rwf) FROM transfers")
        c, mn, mx, s = cur.fetchone()
        ok &= line("transfer count (capture audit)", c, audit["transfer_count"])
        ok &= line("min occurred_at", mn, audit["min_occurred_at"])
        ok &= line("max occurred_at", mx, audit["max_occurred_at"])
        ok &= line("sum amount_rwf", int(s), audit["sum_amount_rwf"])
        cur.execute("SELECT COUNT(*) FROM pg_constraint WHERE connamespace='public'::regnamespace AND NOT convalidated")
        ok &= line("unvalidated constraints", cur.fetchone()[0], 0)
        cur.execute("SELECT round(pg_database_size(current_database())::numeric/1e9, 4)")
        print("database size (GB, 1e9 bytes):", cur.fetchone()[0])
    print("\nALL CHECKS PASSED" if ok else "\nSOME CHECKS FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
