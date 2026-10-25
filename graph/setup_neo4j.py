"""graph/setup_neo4j.py - Section 3.2: unique constraints, range index, wait for ONLINE, show them.

Run with Neo4j started:  python graph/setup_neo4j.py
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from neo4j import GraphDatabase  # noqa: E402
from config import NEO4J_DATABASE, NEO4J_PASSWORD, NEO4J_URI, NEO4J_USER, RESULTS_DIR  # noqa: E402

STATEMENTS = [
    "CREATE CONSTRAINT customer_id_unique IF NOT EXISTS FOR (c:Customer) REQUIRE c.customer_id IS UNIQUE",
    "CREATE CONSTRAINT account_id_unique  IF NOT EXISTS FOR (a:Account)  REQUIRE a.account_id  IS UNIQUE",
    "CREATE CONSTRAINT device_id_unique   IF NOT EXISTS FOR (d:Device)   REQUIRE d.device_id   IS UNIQUE",
    "CREATE RANGE INDEX transfer_occurred_at IF NOT EXISTS FOR ()-[t:TRANSFER]-() ON (t.occurred_at)",
]


def main():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session(database=NEO4J_DATABASE) as s:
        t0 = time.perf_counter()
        for stmt in STATEMENTS:
            print(stmt)
            s.run(stmt).consume()
        print("waiting for indexes to come online ...", flush=True)
        s.run("CALL db.awaitIndexes(7200)").consume()
        secs = round(time.perf_counter() - t0, 2)
        print("\n=== SHOW CONSTRAINTS ===")
        for r in s.run("SHOW CONSTRAINTS YIELD name, type, labelsOrTypes, properties"):
            print(dict(r))
        print("\n=== SHOW INDEXES ===")
        for r in s.run("SHOW INDEXES YIELD name, type, entityType, labelsOrTypes, properties, state"):
            print(dict(r))
    driver.close()
    path = os.path.join(RESULTS_DIR, "neo4j_import.json")
    data = json.load(open(path)) if os.path.exists(path) else {}
    data["constraint_index_seconds"] = secs
    json.dump(data, open(path, "w"), indent=2)
    print(f"constraint + index setup: {secs} s")


if __name__ == "__main__":
    main()
