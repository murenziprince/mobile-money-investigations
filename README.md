# Project 2 - Mobile Money Investigations (PostgreSQL + Neo4j)

Working code for every programming milestone of the handout. Commands below are in **execution order**.
`SCREENSHOTS.md` says exactly when to take each screenshot. `EXPECTED_RESULTS.md` lists the deterministic
answers so you can self-check before screenshotting.

> **What was and was not tested before you got this.** The capture, the PostgreSQL schema/load/indexes, all
> SQL (Q1-Q7, both Q7 versions), the 61-case comparison, benchmark, load test, plots and the independent
> Python reference were run end-to-end on the full 20M-row dataset (PostgreSQL 16). The **Neo4j scripts**
> (`prepare_import.py` output, `graph/*.py`) and the Cypher queries could NOT be run against Neo4j Community
> in the build environment. Cypher Q1, Q3, Q4 (depths 4/6/8), Q5 and the Q6 logic were checked on a different
> openCypher engine (FalkorDB) and matched the independent answers; **Q2 (datetime), Q7 (`shortestPath`),
> Q4 depth 10, `neo4j-admin import` and the Neo4j timings are untested.** Expect to debug those on your
> machine; section "If Neo4j misbehaves" lists the likely spots.

## 0. Prerequisites

* ~10 GB free disk. Python 3.10+. PostgreSQL 15/16 (server + `psql` on PATH). Neo4j **Community 5.x** (needs Java 17/21 - the Neo4j download page says which).
* `pip install -r requirements.txt`
* Keep `mobile_money_generator.py` **unchanged** (`python verify_generator.py` should print UNCHANGED; if your original file has a different hash, put its SHA-256 in `generator.sha256`).

Set secrets as environment variables (placeholders only - never commit real ones). See `.env.example`.

```bash
# Linux / macOS
export PGPASSWORD='your-pg-password' NEO4J_PASSWORD='your-neo4j-password' NEO4J_HOME=/path/to/neo4j-community-5.x.x
```
```powershell
# Windows PowerShell
$env:PGPASSWORD='your-pg-password'; $env:NEO4J_PASSWORD='your-neo4j-password'; $env:NEO4J_HOME='C:\neo4j-community-5.x.x'
```
Optional overrides: `PGHOST PGPORT PGDATABASE PGUSER NEO4J_URI NEO4J_USER NEO4J_DATABASE MM_DATA_DIR`.

## 1. Workspace (Section 1.1)

```bash
createdb -U postgres mobile_money
psql -U postgres -d mobile_money -c "ALTER DATABASE mobile_money SET timezone TO 'Africa/Kigali';"
psql -U postgres -c "SHOW shared_buffers;"      # note your settings; edit postgresql.conf if you tune them, then restart
```
Neo4j (one dedicated instance, default `neo4j` database): unzip Community; set the initial password
**before first start** and set memory in `conf/neo4j.conf` (check `bin/neo4j-admin server memory-recommendation`):
```bash
$NEO4J_HOME/bin/neo4j-admin dbms set-initial-password "$NEO4J_PASSWORD"
# conf/neo4j.conf, e.g. on a 16 GB machine:
#   server.memory.heap.initial_size=4g
#   server.memory.heap.max_size=4g
#   server.memory.pagecache.size=6g
```
Later (once Neo4j is started) run `python record_env.py` - it records OS, CPU, RAM, versions, driver versions and the
database memory settings, and proves both connections work.

## 2. Capture (Section 1.2) - about 1-2 minutes

```bash
python capture.py --preview-only     # dataset_info(), FIELDS, ten records per stream
python capture.py                    # writes data/*.csv + results/capture_audit.json (counts, audit totals, seconds, sizes)
```

## 3. PostgreSQL (Sections 2.1-2.2) - about 2 minutes

```bash
python load_postgres.py              # schema -> \copy load -> FKs + indexes + BRIN + ANALYZE; seconds recorded separately
python check_postgres.py             # counts, 240,000/6,000/2,000 roles, audit totals, no unvalidated constraints
psql -U postgres -d mobile_money -f sql/04_show_schema.sql   # definitions, constraints, indexes, sizes (GB = 1e9 bytes)
```
(Manual equivalent: `psql -d mobile_money -f sql/01_schema.sql`, then `-f sql/02_load.sql` from the project root, then `-f sql/03_constraints_indexes.sql`.)

## 4. Neo4j import (Sections 3.1-3.3)

```bash
python prepare_import.py             # typed temporary copies in data/import_tmp/ (sources untouched) + derived owns.csv
$NEO4J_HOME/bin/neo4j stop           # the project database must be STOPPED and empty
python graph/run_import.py           # neo4j-admin database import full ... ; records seconds, store GB, tx-log GB
$NEO4J_HOME/bin/neo4j console        # (new terminal) start Neo4j; wait for "Started."
python graph/setup_neo4j.py          # 3 unique constraints + range index on TRANSFER.occurred_at, waits until ONLINE
python graph/verify_neo4j.py         # 704,600 nodes / 20,536,900 relationships, roles, owners, audit totals
python prepare_import.py --clean     # only after verify passes: remove the temporary copies
python inspect_account.py 998        # Section 3.3: owner + device + outgoing transfer, SQL JOINs vs Cypher MATCH
```
Windows: use `bin\neo4j.bat` / `bin\neo4j-admin.bat`.

## 5. Questions (Sections 4-5)

`python show_query.py q4` prints a question's SQL/Cypher pair. `python run_questions.py q1 --engine both` runs all six sets in both engines.

```bash
python run_questions.py q1 --engine both
python plots.py q2 --engine pg   &&  python plots.py q2 --engine neo     # 30 days, reconciliation, results/q2_daily.png
python run_questions.py q3 --engine both --rows 10
python plots.py q4 --engine pg   &&  python plots.py q4 --engine neo     # all 24 comparisons, depth plot, one supporting path
python run_questions.py q5 --engine both
python run_questions.py q6 --engine both
python run_questions.py q7 --engine both --q7 v1                         # lengths; improved SQL: --q7 v2
```
Cypher path bounds cannot be parameters in Neo4j, so `{depth}` / `{bound}` are substituted (validated integers) in the Cypher text; everything else uses `$name` parameters. SQL uses psycopg `%(name)s`.

## 6. Correctness (Section 6.1)

```bash
python reference.py --all            # independent answers from the CSVs only (~90 s) -> results/reference_answers.json
python reference.py --checks         # printed evidence: one device overlap, one Q5 chain, one Q6 cycle from CSV rows
python compare.py --engines pg,neo --q7 v1          # 61 cases, exact normalized comparison, Q7 lengths vs supporting paths
python compare.py --engines pg,neo --q7 v1 --brief  # one-screen version (only failures + summary lines)
```
`run_pg(query, params)` / `run_neo(query, params)` are in `db.py` (wrapped in `compare.py`). Full per-case outputs: `results/comparison_<v>.json`.

## 7. Timing (Sections 6.2-6.3) - run ONE database service at a time

Stop Neo4j while timing PostgreSQL, and stop PostgreSQL while timing Neo4j (`pg_ctl stop` / stop the Windows service). Keep resource settings fixed and close other heavy programs.

```bash
python bench.py --engine pg  --q7 v1       # 21 cases x (3 warm-ups + 5 runs) -> results/timing_pg_v1.csv   (Q7 bound 6 is slow in v1)
python bench.py --engine neo               # -> results/timing_neo.csv
python bench.py --plans --engine pg --q7 v1    # EXPLAIN (ANALYZE, BUFFERS): Q2, Q4-B depth 10, Q7-B bound 6 (v1 and v2) -> plans/
python bench.py --plans --engine neo           # PROFILE for the same three -> plans/
# 6.3 improvement (queries/q7_v2.sql, bidirectional search):
python compare.py --engines pg --q7 v2         # recheck all 12 Q7 cases (+ the other 49)
python bench.py --engine pg --q7 v2 --only Q7  # the four revised SQL cases -> results/timing_pg_v2.csv
python bench.py --summary                      # median/min/max ms, PG/Neo median ratios -> results/timing_summary.csv
```
Timeouts and errors are stored with their status and excluded from medians. If v2 does not help in your run, say so: a justified unsuccessful attempt can earn full marks.

## 8. Concurrency (Sections 7.1-7.2) - again ONE database at a time

```bash
python loadtest.py --engine pg  --q7 v2     # use the SQL Q7 version you selected in 6.3 (v1 or v2); ~8 min per engine
python loadtest.py --engine neo
python loadtest.py --summary                # medians of 3 repetitions: the 16 combinations
python plots.py scaling                     # throughput and p95 vs clients -> results/scaling.png
```
(`MM_LOAD_SECONDS=4` shortens the 15 s window for a smoke test only - never for submitted numbers.)

## 9. Submission (Sections 9.1-9.2)

* GitHub repo + matching ZIP: everything in this folder **except** `data/` and the database stores (`.gitignore` handles it). Keep `results/` and `plans/`.
* `python verify_generator.py` -> UNCHANGED. Placeholders only in the repo (no real passwords).
* Rerun `python compare.py --engines pg,neo` and screenshot completion; then stop both services and screenshot the stopped status (`pg_ctl status`, `neo4j status`). Keep your stores.

## Layout

| File | Purpose |
|---|---|
| `capture.py`, `config.py` | 1.2 capture; shared settings, review sets A-F, CAT time-window helper |
| `sql/01..04_*.sql`, `load_postgres.py`, `check_postgres.py` | 2.1-2.2 |
| `prepare_import.py`, `graph/*.py` | 3.2 typed CSV copies, import, constraints, verification |
| `queries/*.sql|*.cypher`, `queries.py`, `run_questions.py`, `show_query.py` | Q1-Q7 pairs and runners |
| `db.py`, `compare.py`, `reference.py` | `run_pg`/`run_neo`, 61-case comparison, independent CSV reference |
| `bench.py`, `loadtest.py`, `plots.py` | 6.2-6.3, 7.1-7.2, charts |

## If Neo4j misbehaves (untested here)

* **Import syntax**: `graph/run_import.py` uses Neo4j 5 syntax (`neo4j-admin database import full neo4j --overwrite-destination ...`). It switches to 4.4 syntax if `--version` starts with `4.`. If your version rejects an option, run `neo4j-admin database import full --help`.
* **Q7**: the `all(n IN nodes(p) WHERE ...)` predicate on `shortestPath` is meant to be applied during the search. Check `PROFILE` for a filter *after* the shortest-path operator; if you are on 5.21+ the quantified-path alternative is in `queries/q7.cypher` comments.
* **Q4 depth 10** may time out if the planner enumerates trails instead of using a pruning expansion (`PruningVarExpand` in PROFILE). A timeout is a valid recorded result.
* **Q6** relies on `all(r IN ts WHERE ...)` being inlined into the variable-length expansion; if PROFILE shows no pruning and it is slow, that is a finding to report.
* **`verify_neo4j.py`** `count(DISTINCT t.transfer_id)` needs heap for 20M ids; it falls back to a min/max/count test automatically.
