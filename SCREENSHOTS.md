# Screenshot guide - where and when

**Rules for every screenshot** (handout, page 1): the **command you typed**, its **result**, and the **taskbar with the clock** must all be visible. Use a full-screen terminal with a large font. Where a command prints one block per review set, one screenshot of the whole block is enough ("consolidate repeated cases"). If output is longer than a screen, take two consecutive screenshots, or use the `--rows` / `--brief` options noted below. Full outputs go in the code submission, not the report.

Take each screenshot **right after** the command finishes, in the order below. "Report §" is where it belongs in your PDF (milestone order).

| # | When (after this step) | Command | Must be visible | Handout § |
|---|---|---|---|---|
| 1 | Both databases running | `python record_env.py` | "PostgreSQL connection OK", "Neo4j connection OK", versions, CPU, RAM, OS, memory settings, timezone `Africa/Kigali` | 1.1 |
| 2 | Before capture | `python capture.py --preview-only` (2 shots: info+FIELDS, then the 5 previews) | `dataset_info()`, `FIELDS`, ten records from each stream | 1.2 |
| 3 | Capture finished | `python capture.py` | five `OK` lines, the five-stream totals table, audit line, total 20,993,500, capture seconds, CSV sizes | 1.2 |
| 4 | Schema created | `psql -U postgres -d mobile_money -f sql/04_show_schema.sql` (top part) | `\d` of all five tables and the constraints list (PK, FK, CHECK, `convalidated = t`) | 2.1 |
| 5 | Load finished | `python load_postgres.py` | `COPY` counts, "bulk load" seconds and "FKs + indexes" seconds as two separate numbers | 2.2 |
| 6 | Same | `python check_postgres.py` then the lower part of `04_show_schema.sql` | all `OK`, role counts, indexes list, sizes in GB, database size | 2.2 |
| 7 | Typed copies created | `python prepare_import.py` | six files written, header lines (also `head -2 data/import_tmp/*.csv`) | 3.2 |
| 8 | Neo4j stopped | `python graph/run_import.py` | the full `neo4j-admin ... import full ... --id-type=integer --nodes=... --relationships=...` command, the completion message, seconds, store GB, tx-log GB | 3.2 |
| 9 | Neo4j started | `python graph/setup_neo4j.py` | the 3 constraints, the range index, all indexes `ONLINE`, setup seconds | 3.2 |
| 10 | Same | `python graph/verify_neo4j.py` | all `OK`: 704,600 nodes, 20,536,900 relationships, roles, one owner, unique transfer_id, audit totals. Then run `python prepare_import.py --clean` (include it in the same shot or the next) | 3.2 |
| 11 | Both DBs up | `python inspect_account.py 998` | matching SQL-JOIN rows and Cypher-MATCH rows for the same owner/device/transfer | 3.3 |
| 12 | | `python show_query.py q1` then `python run_questions.py q1 --engine both` | six sets, both engines, `MATCH` per set, the CAT window | 4.1 |
| 13 | | `python plots.py q2 --engine pg` and `--engine neo` | 30 rows (use two shots), the three reconciliation `OK` lines. Then open `results/q2_daily.png` | 4.2 |
| 14 | | `python run_questions.py q3 --engine both --rows 10` | six sets, counts and rows, `MATCH` | 4.3 |
| 15 | | `python show_query.py q4` (query pair) | SQL recursive CTE + Cypher pattern | 5.1 |
| 16 | | `python plots.py q4 --engine pg` (and `neo`) | all 24 case lines, then the supporting path line; open `results/q4_depth.png`. **Write down your depth 8 / 10 predictions BEFORE running this** | 5.1 |
| 17 | | `python show_query.py q5`, `python run_questions.py q5 --engine both` | query pair + six counts both engines | 5.2 |
| 18 | | `python reference.py --checks` | one Q5 chain: IDs, CAT times, amounts, gaps, ratios; one Q6 cycle; the device-overlap check | 5.2, 5.3, 6.1 |
| 19 | | `python show_query.py q6`, `python run_questions.py q6 --engine both` | query pair + six counts both engines | 5.3 |
| 20 | | `python show_query.py q7`, `python run_questions.py q7 --engine both --q7 v1` | the 12 length comparisons (two shots) | 5.4 |
| 21 | | `python compare.py --engines pg,neo --q7 v1 --brief` (plus a full run once for the full table) | per-question `x/x` lines, `TOTAL: 61/61`, Q7 supporting-path validation lines | 6.1, 5.4 |
| 22 | PG only running | `python bench.py --engine pg --q7 v1` (screenshot the end) | last cases finishing; then `python bench.py --summary` | 6.2 |
| 23 | Neo4j only running | `python bench.py --engine neo`, then `python bench.py --summary` | the summary table with median/min/max and the PG/Neo ratio column | 6.2 |
| 24 | | `python bench.py --plans --engine pg` and `--engine neo`; then `type plans\pg_Q7-B-b6_v1.txt` (Windows) / `head -60 plans/pg_Q7-B-b6_v1.txt` | the plan tree with row counts and buffers/db hits for Q2, Q4-B d10, Q7-B b6 | 6.2 |
| 25 | | `python compare.py --engines pg --q7 v2`, then `python bench.py --engine pg --q7 v2 --only Q7`, then `python bench.py --summary` | all 12 Q7 cases still correct; four revised timings; before/after plans (`plans/pg_Q7-B-b6_v1.txt` vs `_v2.txt`) | 6.3 |
| 26 | One DB at a time | `python loadtest.py --engine pg --q7 <selected>` — **while it runs** take a shot showing the line `active clients now: N/N` for 16 clients, ideally with Task Manager / `htop` open beside it | active clients, per-repetition results | 7.1 |
| 27 | Both engines finished | `python loadtest.py --summary` | all 16 combination rows | 7.1 |
| 28 | | `python plots.py scaling`; open `results/scaling.png` | throughput and p95 vs clients, both engines, both workloads | 7.2 |
| 29 | Final | `python compare.py --engines pg,neo` (the submitted 61-case rerun) | completion with `TOTAL: 61/61` | 9.2 |
| 30 | Final | stop both services, then `pg_ctl status` / Windows Services view and `neo4j status` | both reported **stopped** | 9.2 |

## Things you must draw / write yourself (no code can do these)
* §2.1 schema diagram + field meanings and units; §3.1 graph schema diagram + mapping of every source field.
* §4.1 why outgoing value is not a balance; §4.2 one pattern + why value is not revenue; §4.3 a legitimate sharing scenario and why overlap is not simultaneous use; §5 all "explain" items.
* §8.1 priorities for A/D, B/E, C/F with IDs, amounts, times, device evidence; §8.2 recommendation (≤ 500 words); §8.3 your own 150–200 named words, contributions, and the LLM-assistance disclosure.

## Suggested time plan (today is Wed 21 Oct; due Mon 26 Oct 11:59 PM)
| Day | Do | Run time on a mid-range laptop (my test) |
|---|---|---|
| Wed 21 | Install, steps 1-6 (capture, PostgreSQL), Neo4j install + import (steps 7-11) | capture ≈ 1-2 min, load+indexes ≈ 1-2 min, Neo4j import: unknown, budget 10-30 min |
| Thu 22 | Q1-Q7 screenshots both engines (12-21), fix any Cypher issues | PG side ≈ seconds-to-minutes; Q7 v1 bound 6 ≈ 20+ s per set |
| Fri 23 | Benchmarks (22-25) | PG v1 ≈ 10 min, Neo similar or less; one DB at a time |
| Sat 24 | Load tests + plots (26-28) | ≈ 8 min per engine |
| Sun 25 | Report: diagrams, explanations, §8; individual notes (each member) | |
| Mon 26 | Final rerun + stopped-service shots (29-30), submit PDF + GitHub URL + ZIP before 23:59 | |
