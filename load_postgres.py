"""load_postgres.py - Section 2: create schema, bulk-load, then build constraints/indexes, timing each phase.

Usage (from the project root, after capture.py):  python load_postgres.py
Equivalent manual commands are in README.md. psql must be on PATH.
Writes results/pg_load.json (loading seconds and constraint/index seconds, recorded separately).
"""
import json
import os
import subprocess
import sys
import time

from config import PG, RESULTS_DIR, ROOT


def psql(args):
    env = dict(os.environ, PGPASSWORD=PG["password"])
    cmd = ["psql", "-h", PG["host"], "-p", str(PG["port"]), "-U", PG["user"], "-d", PG["dbname"],
           "-v", "ON_ERROR_STOP=1"] + args
    print("$", " ".join(cmd), flush=True)
    r = subprocess.run(cmd, cwd=ROOT, env=env)
    if r.returncode != 0:
        sys.exit(f"psql failed with exit code {r.returncode}")


def timed(label, args):
    t0 = time.perf_counter()
    psql(args)
    s = round(time.perf_counter() - t0, 2)
    print(f"==> {label}: {s} s\n", flush=True)
    return s


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    out = {}
    psql(["-f", "sql/01_schema.sql"])
    out["load_seconds"] = timed("bulk load (5 x \\copy)", ["-f", "sql/02_load.sql"])
    out["constraint_index_seconds"] = timed("FKs + indexes + BRIN + ANALYZE",
                                            ["-f", "sql/03_constraints_indexes.sql"])
    with open(os.path.join(RESULTS_DIR, "pg_load.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
