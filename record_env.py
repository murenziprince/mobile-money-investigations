"""record_env.py - Section 1.1: record CPU, RAM, OS, software/driver versions and database memory settings.

  python record_env.py            # prints everything and writes results/environment.json
Run it with BOTH databases up, then screenshot the output (connections succeed = the settings print).
"""
import json
import os
import platform
import sys

from config import NEO4J_DATABASE, RESULTS_DIR


def total_ram_gb():
    try:
        import psutil
        return round(psutil.virtual_memory().total / 1e9, 2)
    except Exception:
        pass
    try:
        with open("/proc/meminfo") as f:
            return round(int(f.readline().split()[1]) * 1024 / 1e9, 2)
    except Exception:
        pass
    try:
        import ctypes
        class MS(ctypes.Structure):
            _fields_ = [("l", ctypes.c_ulong), ("m", ctypes.c_ulong), ("tp", ctypes.c_ulonglong)] + \
                       [(f"x{i}", ctypes.c_ulonglong) for i in range(5)]
        ms = MS(); ms.l = ctypes.sizeof(MS)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms))
        return round(ms.tp / 1e9, 2)
    except Exception:
        return None


def cpu_name():
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return platform.processor() or "unknown"


def main():
    info = dict(os=f"{platform.system()} {platform.release()} ({platform.version()[:60]})",
                cpu=cpu_name(), logical_cores=os.cpu_count(), ram_gb=total_ram_gb(),
                python=sys.version.split()[0])
    for mod in ("psycopg", "neo4j", "numpy", "matplotlib"):
        try:
            info[f"{mod}_version"] = __import__(mod).__version__
        except Exception:
            info[f"{mod}_version"] = "not installed"
    try:
        import db
        conn = db.pg_connect()
        info["postgresql_version"] = conn.execute("SELECT version()").fetchone()[0]
        info["postgresql_settings"] = {k: conn.execute(f"SHOW {k}").fetchone()[0] for k in
            ("timezone", "shared_buffers", "work_mem", "effective_cache_size", "maintenance_work_mem",
             "max_parallel_workers_per_gather", "max_connections")}
        print("PostgreSQL connection OK")
    except Exception as e:
        info["postgresql_error"] = f"{type(e).__name__}: {e}"
    try:
        s = db.neo_session()
        info["neo4j_database"] = NEO4J_DATABASE
        info["neo4j_components"] = [dict(name=r["name"], versions=r["versions"], edition=r["edition"])
                                    for r in s.run("CALL dbms.components() YIELD name, versions, edition")]
        info["neo4j_memory_settings"] = {r["name"]: r["value"] for r in
                                         s.run("CALL dbms.listConfig('memory') YIELD name, value")}
        print("Neo4j connection OK")
    except Exception as e:
        info["neo4j_error"] = f"{type(e).__name__}: {e}"
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(os.path.join(RESULTS_DIR, "environment.json"), "w") as f:
        json.dump(info, f, indent=2)
    print(json.dumps(info, indent=2))


if __name__ == "__main__":
    main()
