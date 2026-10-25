"""graph/run_import.py - Section 3.2: full neo4j-admin import into the (stopped, empty) default database.

  set NEO4J_HOME to your Neo4j Community folder, STOP the server, then:  python graph/run_import.py
Records import seconds and store/transaction-log sizes in results/neo4j_import.json.
Works with Neo4j 5.x / 2025.x syntax; Neo4j 4.4 syntax is selected automatically from --version.
"""
import json
import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATA_DIR, NEO4J_DATABASE, RESULTS_DIR  # noqa: E402

TMP = os.path.join(DATA_DIR, "import_tmp")


def admin_path():
    home = os.environ.get("NEO4J_HOME")
    if not home:
        sys.exit("Set NEO4J_HOME to the Neo4j Community folder first (see README).")
    exe = shutil.which("neo4j-admin", path=os.path.join(home, "bin")) or shutil.which("neo4j-admin.bat", path=os.path.join(home, "bin"))
    if not exe:
        sys.exit(f"neo4j-admin not found under {home}/bin")
    return home, exe


def dir_gb(path):
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            total += os.path.getsize(os.path.join(root, f))
    return round(total / 1_000_000_000, 4)


def main():
    home, exe = admin_path()
    ver = subprocess.run([exe, "--version"], capture_output=True, text=True).stdout.strip()
    print("neo4j-admin version:", ver)
    f = lambda n: os.path.join(TMP, n)
    parts = [
        f"--nodes=Customer={f('customers.csv')}", f"--nodes=Account={f('accounts.csv')}",
        f"--nodes=Device={f('devices.csv')}",
        f"--relationships=OWNS={f('owns.csv')}", f"--relationships=USED_DEVICE={f('used_device.csv')}",
        f"--relationships=TRANSFER={f('transfer.csv')}",
    ]
    if ver.startswith("4."):
        cmd = [exe, "import", f"--database={NEO4J_DATABASE}", "--id-type=integer", "--skip-duplicate-nodes=false"] + parts
    else:
        cmd = [exe, "database", "import", "full", NEO4J_DATABASE, "--overwrite-destination",
               "--id-type=integer"] + parts
    print("$", " ".join(cmd), flush=True)
    t0 = time.perf_counter()
    rc = subprocess.run(cmd).returncode
    secs = round(time.perf_counter() - t0, 2)
    if rc != 0:
        sys.exit(f"import failed (exit {rc}). Is the server stopped and the database empty?")
    out = dict(import_seconds=secs,
               store_gb=dir_gb(os.path.join(home, "data", "databases", NEO4J_DATABASE)),
               transaction_log_gb=dir_gb(os.path.join(home, "data", "transactions", NEO4J_DATABASE)),
               neo4j_admin_version=ver)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(os.path.join(RESULTS_DIR, "neo4j_import.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps(out, indent=2))
    print("Now START Neo4j, then run: python graph/setup_neo4j.py")


if __name__ == "__main__":
    main()
