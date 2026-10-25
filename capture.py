"""capture.py - Section 1.2: stream the generator into CSV files with audit totals.

Run:   python capture.py --preview-only     # screenshot 1: dataset_info, FIELDS, 10 records/stream
       python capture.py                    # screenshot 2: completed five-stream totals
Needs mobile_money_generator.py (unchanged) in this folder.
Outputs (in data/ - keep local, never commit): customers.csv, accounts.csv, devices.csv,
        account_devices.csv, transfers.csv; results/capture_audit.json (used to verify both DBs).
"""
import csv
import json
import os
import sys
import time
from itertools import islice

import mobile_money_generator as g
from config import AUDIT_FILE, DATA_DIR, RESULTS_DIR

STREAMS = {
    "customers": g.iter_customers,
    "accounts": g.iter_accounts,
    "devices": g.iter_devices,
    "account_devices": g.iter_account_devices,
    "transfers": g.iter_transfers,
}


def preview():
    info = g.dataset_info()
    print("dataset_info():")
    print(json.dumps(info, indent=2, default=str))
    print("\ng.FIELDS:")
    for name, fields in g.FIELDS.items():
        print(f"  {name}: {fields}")
    for name, make_iter in STREAMS.items():
        print(f"\n--- first 10 records of {name} ---")
        for row in islice(make_iter(), 10):  # a fresh iterator call restarts the stream
            print(row)


def capture_stream(name, make_iter):
    fields = g.FIELDS[name]
    path = os.path.join(DATA_DIR, f"{name}.csv")
    consumed = written = 0
    audit = {"min_occurred_at": None, "max_occurred_at": None, "sum_amount_rwf": 0}
    t0 = time.perf_counter()
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in make_iter():  # streamed: the full stream is never held in memory
            consumed += 1
            writer.writerow(row)
            written += 1
            if name == "transfers":
                t = row["occurred_at"]
                if audit["min_occurred_at"] is None or t < audit["min_occurred_at"]:
                    audit["min_occurred_at"] = t
                if audit["max_occurred_at"] is None or t > audit["max_occurred_at"]:
                    audit["max_occurred_at"] = t
                audit["sum_amount_rwf"] += row["amount_rwf"]
                if consumed % 1_000_000 == 0:
                    print(f"  transfers: {consumed:,} rows, "
                          f"{time.perf_counter() - t0:,.1f}s elapsed", flush=True)
    seconds = time.perf_counter() - t0
    size = os.path.getsize(path)
    result = {"file": path, "consumed": consumed, "written": written,
              "seconds": round(seconds, 2), "size_bytes": size,
              "size_gb": round(size / 1_000_000_000, 4)}  # 1 GB = 1,000,000,000 bytes
    if name == "transfers":
        result["transfer_count"] = written
        result.update(audit)
    return result


def main():
    preview()
    if "--preview-only" in sys.argv:
        return
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    expected = g.dataset_info()["expected_counts"]
    report = {}
    total_t0 = time.perf_counter()
    for name, make_iter in STREAMS.items():
        print(f"\nCapturing {name} ...", flush=True)
        report[name] = capture_stream(name, make_iter)
        r = report[name]
        ok = r["consumed"] == r["written"] == expected[name]
        print(f"  {name}: consumed={r['consumed']:,} written={r['written']:,} "
              f"expected={expected[name]:,} {'OK' if ok else 'MISMATCH'} "
              f"({r['seconds']}s, {r['size_gb']} GB)", flush=True)
    report["total_seconds"] = round(time.perf_counter() - total_t0, 2)
    report["total_rows"] = sum(report[n]["written"] for n in STREAMS)
    report["total_gb"] = round(sum(report[n]["size_bytes"] for n in STREAMS) / 1e9, 4)
    with open(AUDIT_FILE, "w") as f:
        json.dump(report, f, indent=2)

    print("\n=== Five-stream totals ===")
    for name in STREAMS:
        r = report[name]
        print(f"{name:16s} rows={r['written']:>12,}  {r['size_gb']:>8} GB  {r['seconds']:>9}s")
    t = report["transfers"]
    print(f"transfer audit: count={t['transfer_count']:,} "
          f"min_occurred_at={t['min_occurred_at']} max_occurred_at={t['max_occurred_at']} "
          f"sum_amount_rwf={t['sum_amount_rwf']:,}")
    print(f"total source records: {report['total_rows']:,} (handout: 20,993,500)")
    print(f"total CSV size: {report['total_gb']} GB | total capture seconds: {report['total_seconds']}")
    if report["total_rows"] != 20_993_500:
        print("WARNING: total does not match the handout!")


if __name__ == "__main__":
    main()
