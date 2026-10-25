"""prepare_import.py - Section 3.2: temporary Neo4j-typed copies of the CSVs (sources stay unchanged).

  python prepare_import.py          # create data/import_tmp/*.csv
  python prepare_import.py --clean  # remove the temporary copies after the import has been verified
Header mapping (source field -> graph):
  customers.csv        customer_id:ID(Customer), region:string                      -> (:Customer)
  accounts.csv         account_id:ID(Account), :IGNORE, role:string                  -> (:Account)  [customer_id ignored here]
  devices.csv          device_id:ID(Device), access_type:string                      -> (:Device)
  owns.csv (derived)   :START_ID(Customer), :END_ID(Account)                         -> (Customer)-[:OWNS]->(Account)
  used_device.csv      :START_ID(Account), :END_ID(Device), first_day:int, last_day:int, observations:int -> -[:USED_DEVICE]->
  transfer.csv         transfer_id:long, :START_ID(Account), :END_ID(Account), occurred_at:long, amount_rwf:int -> -[:TRANSFER]->
"""
import csv
import os
import shutil
import sys
import time

from config import DATA_DIR

TMP = os.path.join(DATA_DIR, "import_tmp")

HEADERS = {
    "customers": "customer_id:ID(Customer),region:string",
    "accounts": "account_id:ID(Account),:IGNORE,role:string",
    "devices": "device_id:ID(Device),access_type:string",
    "account_devices": ":START_ID(Account),:END_ID(Device),first_day:int,last_day:int,observations:int",
    "transfers": "transfer_id:long,:START_ID(Account),:END_ID(Account),occurred_at:long,amount_rwf:int",
}
OUT_NAMES = {"customers": "customers.csv", "accounts": "accounts.csv", "devices": "devices.csv",
             "account_devices": "used_device.csv", "transfers": "transfer.csv"}


def copy_with_header(name):
    src = os.path.join(DATA_DIR, f"{name}.csv")
    dst = os.path.join(TMP, OUT_NAMES[name])
    t0 = time.perf_counter()
    with open(src, "rb") as fi, open(dst, "wb") as fo:
        fi.readline()                                   # drop the source header, keep every data row
        fo.write(HEADERS[name].encode() + b"\n")
        shutil.copyfileobj(fi, fo, 16 * 1024 * 1024)
    print(f"  {OUT_NAMES[name]:16s} {os.path.getsize(dst) / 1e9:.4f} GB  {time.perf_counter() - t0:.1f}s")


def derive_owns():
    """OWNS: one (customer_id, account_id) row per account, sorted by customer_id then account_id."""
    with open(os.path.join(DATA_DIR, "accounts.csv"), newline="") as f:
        r = csv.reader(f)
        next(r)
        pairs = sorted((int(c), int(a)) for a, c, _ in r)
    dst = os.path.join(TMP, "owns.csv")
    with open(dst, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([":START_ID(Customer)", ":END_ID(Account)"])
        w.writerows(pairs)
    print(f"  owns.csv         {len(pairs):,} rows (derived from accounts.csv)")


def main():
    if "--clean" in sys.argv:
        shutil.rmtree(TMP, ignore_errors=True)
        print("removed", TMP)
        return
    os.makedirs(TMP, exist_ok=True)
    print("Writing typed import copies to", TMP)
    for name in HEADERS:
        copy_with_header(name)
    derive_owns()
    print("done. Source CSVs in", DATA_DIR, "were not modified.")


if __name__ == "__main__":
    main()
