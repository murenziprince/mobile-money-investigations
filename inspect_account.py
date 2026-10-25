"""inspect_account.py - Section 3.3: trace one loaded account to its owner, a device and an outgoing transfer.

  python inspect_account.py [account_id] [--engine pg|neo|both]     (default account 998, both engines)
Screenshot the two matching record sets. Foreign keys become relationships:
  accounts.customer_id -> (Customer)-[:OWNS]->(Account);  account_devices -> (Account)-[:USED_DEVICE]->(Device);
  transfers.sender_id/receiver_id -> (Account)-[:TRANSFER]->(Account), one relationship per transfer row.
"""
import sys

import db
from config import cat_str

SQL = """
SELECT a.account_id, a.role, c.customer_id, c.region, d.device_id, d.access_type,
       ad.first_day, ad.last_day, ad.observations, t.transfer_id, t.receiver_id, t.occurred_at, t.amount_rwf
FROM accounts a
JOIN customers c       ON c.customer_id = a.customer_id
JOIN account_devices ad ON ad.account_id = a.account_id
JOIN devices d         ON d.device_id = ad.device_id
JOIN LATERAL (SELECT * FROM transfers t WHERE t.sender_id = a.account_id ORDER BY t.occurred_at LIMIT 1) t ON TRUE
WHERE a.account_id = %(account)s
ORDER BY d.device_id
LIMIT 3
"""
CYPHER = """
MATCH (c:Customer)-[:OWNS]->(a:Account {account_id:$account})-[u:USED_DEVICE]->(d:Device)
MATCH (a)-[t:TRANSFER]->(b:Account)
WITH c, a, u, d, t, b ORDER BY d.device_id, t.occurred_at
RETURN a.account_id AS account_id, a.role AS role, c.customer_id AS customer_id, c.region AS region,
       d.device_id AS device_id, d.access_type AS access_type, u.first_day AS first_day, u.last_day AS last_day,
       u.observations AS observations, t.transfer_id AS transfer_id, b.account_id AS receiver_id,
       t.occurred_at AS occurred_at, t.amount_rwf AS amount_rwf
LIMIT 3
"""
COLS = "account role customer region device access first last obs transfer receiver occurred_at amount".split()


def show(engine, rows):
    print(f"--- {engine} ---")
    print("  " + " | ".join(COLS))
    for r in rows:
        print("  " + " | ".join(str(x) for x in r), "  (", cat_str(r[11]), ")")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    account = int(args[0]) if args else 998
    engine = sys.argv[sys.argv.index("--engine") + 1] if "--engine" in sys.argv else "both"
    print(f"Tracing account {account}: owner, a device, an outgoing transfer")
    if engine in ("pg", "both"):
        show("PostgreSQL (JOINs)", db.run_pg(SQL, {"account": account}))
    if engine in ("neo", "both"):
        show("Neo4j (MATCH)", db.run_neo(CYPHER, {"account": account}))
    db.close_all()


if __name__ == "__main__":
    main()
