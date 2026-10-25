"""config.py - shared settings, review sets and time helpers.

Secrets are read from environment variables. Defaults are PLACEHOLDERS only:
set them in your shell (see README.md), never commit real passwords.
"""
import os
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("MM_DATA_DIR", os.path.join(ROOT, "data"))
RESULTS_DIR = os.path.join(ROOT, "results")
PLANS_DIR = os.path.join(ROOT, "plans")
AUDIT_FILE = os.path.join(RESULTS_DIR, "capture_audit.json")

# ---- PostgreSQL (placeholders; override with environment variables) ----
PG = dict(
    host=os.environ.get("PGHOST", "localhost"),
    port=int(os.environ.get("PGPORT", "5432")),
    dbname=os.environ.get("PGDATABASE", "mobile_money"),
    user=os.environ.get("PGUSER", "postgres"),
    password=os.environ.get("PGPASSWORD", "CHANGE_ME_PG_PASSWORD"),
)

# ---- Neo4j Community (placeholders) ----
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "CHANGE_ME_NEO4J_PASSWORD")
NEO4J_DATABASE = os.environ.get("NEO4J_DATABASE", "neo4j")

TZ = ZoneInfo("Africa/Kigali")

# Review sets from the handout: label -> (review account, destination, September day)
SETS = {
    "A": dict(account=998,    destination=24755,  day=6),
    "B": dict(account=147228, destination=186823, day=13),
    "C": dict(account=206978, destination=6573,   day=8),
    "D": dict(account=237998, destination=21755,  day=6),
    "E": dict(account=144228, destination=183823, day=13),
    "F": dict(account=203978, destination=3573,   day=8),
}


def hour_window(day):
    """09:45:00 inclusive to 10:45:00 exclusive CAT on 2026-09-<day>, as epoch seconds."""
    s = datetime(2026, 9, day, 9, 45, 0, tzinfo=TZ)
    e = datetime(2026, 9, day, 10, 45, 0, tzinfo=TZ)
    return int(s.timestamp()), int(e.timestamp())


def set_params(label):
    """Parameter dict for one review set (account, destination, day, start, end)."""
    p = dict(SETS[label])
    p["start"], p["end"] = hour_window(p["day"])
    return p


def cat_str(epoch):
    """Epoch seconds -> 'YYYY-MM-DD HH:MM:SS CAT' for evidence tables."""
    return datetime.fromtimestamp(epoch, TZ).strftime("%Y-%m-%d %H:%M:%S CAT")


if __name__ == "__main__":
    for k in SETS:
        p = set_params(k)
        print(k, p, cat_str(p["start"]), "->", cat_str(p["end"]))
