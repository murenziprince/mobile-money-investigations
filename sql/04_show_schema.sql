-- 04_show_schema.sql  (Section 2.1 screenshot) - definitions, constraints, validation, indexes, sizes.
\echo '=== table definitions ==='
\d customers
\d devices
\d accounts
\d account_devices
\d transfers

\echo '=== constraints (convalidated = t means validated) ==='
SELECT conrelid::regclass AS table_name, conname, contype, convalidated, pg_get_constraintdef(oid) AS definition
FROM pg_constraint
WHERE connamespace = 'public'::regnamespace AND contype IN ('p', 'f', 'c')
ORDER BY conrelid::regclass::text, contype, conname;

\echo '=== indexes ==='
SELECT tablename, indexname, indexdef FROM pg_indexes WHERE schemaname = 'public' ORDER BY tablename, indexname;

\echo '=== sizes (1 GB = 1,000,000,000 bytes) ==='
SELECT c.relname AS relation,
       round(pg_table_size(c.oid)::numeric / 1e9, 4)   AS table_gb,
       round(pg_indexes_size(c.oid)::numeric / 1e9, 4) AS index_gb,
       round(pg_total_relation_size(c.oid)::numeric / 1e9, 4) AS total_gb
FROM pg_class c WHERE c.relnamespace = 'public'::regnamespace AND c.relkind = 'r' ORDER BY c.relname;
SELECT round(pg_database_size(current_database())::numeric / 1e9, 4) AS database_gb;

\echo '=== settings ==='
SHOW timezone;
SHOW shared_buffers;
SHOW work_mem;
SHOW effective_cache_size;
SHOW max_parallel_workers_per_gather;
SELECT version();
