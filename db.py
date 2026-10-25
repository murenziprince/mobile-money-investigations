"""db.py - persistent connections plus run_pg / run_neo (Section 6.1) and result normalization.

run_pg(query, params) and run_neo(query, params) each return EVERY result row as a list of tuples.
Both keep one persistent connection per process. Optional timeout_s enforces the 60 s / 180 s limits.
"""
import datetime
import decimal

import psycopg

from config import NEO4J_DATABASE, NEO4J_PASSWORD, NEO4J_URI, NEO4J_USER, PG

_pg = None
_neo_driver = None
_neo_session = None
_pg_timeout = None


def pg_connect():
    """Persistent autocommit connection; prepare_threshold=None keeps every run on a fresh custom plan."""
    global _pg, _pg_timeout
    if _pg is None or _pg.closed:
        _pg = psycopg.connect(**PG, autocommit=True, prepare_threshold=None)
        _pg_timeout = None
    return _pg


def neo_session():
    global _neo_driver, _neo_session
    if _neo_session is None:
        from neo4j import GraphDatabase
        _neo_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        _neo_session = _neo_driver.session(database=NEO4J_DATABASE)
    return _neo_session


def run_pg(query, params=None, timeout_s=None):
    global _pg_timeout
    conn = pg_connect()
    if timeout_s != _pg_timeout:
        conn.execute(f"SET statement_timeout = {int((timeout_s or 0) * 1000)}")
        _pg_timeout = timeout_s
    with conn.cursor() as cur:
        cur.execute(query, params or {})
        return [tuple(r) for r in cur.fetchall()] if cur.description else []


def run_neo(query, params=None, timeout_s=None):
    from neo4j import Query
    session = neo_session()
    q = Query(query, timeout=timeout_s) if timeout_s else query
    result = session.run(q, params or {})
    return [tuple(r.values()) for r in result]  # consume every row before returning


def close_all():
    global _pg, _neo_driver, _neo_session
    if _pg is not None and not _pg.closed:
        _pg.close()
    if _neo_session is not None:
        _neo_session.close()
    if _neo_driver is not None:
        _neo_driver.close()
    _pg = _neo_driver = _neo_session = None


def is_timeout(exc):
    text = f"{type(exc).__name__} {exc}".lower()
    return "timeout" in text or "timed out" in text or "canceling statement" in text or "querycanceled" in text


# ---------------- normalization & exact comparison ----------------
def _norm(v):
    if isinstance(v, bool) or v is None or isinstance(v, str):
        return v
    if isinstance(v, int):
        return int(v)
    if isinstance(v, float):
        return int(v) if v.is_integer() else v
    if isinstance(v, decimal.Decimal):
        return int(v) if v == v.to_integral_value() else float(v)
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.isoformat()
    if hasattr(v, "iso_format"):          # neo4j.time.Date / DateTime
        return v.iso_format()
    if isinstance(v, (list, tuple)):
        return tuple(_norm(x) for x in v)
    return str(v)


def normalize(rows):
    """Integers to int, dates to ISO strings, lists to tuples, rows sorted: ready for exact ==."""
    return sorted((tuple(_norm(x) for x in r) for r in rows), key=repr)


def canon(case, rows):
    """Normalize one case's rows. Q7 length: 'no route' is [(None,)] in SQL and [] in Cypher; unify to [(None,)]."""
    out = normalize(rows)
    if case["q"] == "Q7" and not out:
        out = [(None,)]
    return out
