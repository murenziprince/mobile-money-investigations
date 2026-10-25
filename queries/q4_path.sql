-- Q4 supporting path (SQL): ONE path of exactly %(depth)s links from the review account to another account,
-- every node typed (Customer 7 is not Account 7), no node repeated. Use a small depth (e.g. 4 or 6) for evidence.
WITH RECURSIVE edges(sk, si, dk, di) AS (
    SELECT 'Customer', customer_id, 'Account',  account_id  FROM accounts
    UNION ALL SELECT 'Account',  account_id,  'Customer', customer_id FROM accounts
    UNION ALL SELECT 'Account',  account_id,  'Device',   device_id   FROM account_devices
    UNION ALL SELECT 'Device',   device_id,   'Account',  account_id  FROM account_devices
), walk(kind, id, depth, path) AS (
    SELECT 'Account', %(account)s::integer, 0, ARRAY['Account:' || %(account)s::text]
  UNION ALL
    SELECT e.dk, e.di, w.depth + 1, w.path || (e.dk || ':' || e.di)
    FROM walk w JOIN edges e ON e.sk = w.kind AND e.si = w.id
    WHERE w.depth < %(depth)s AND NOT ((e.dk || ':' || e.di) = ANY (w.path))
)
SELECT path FROM walk WHERE kind = 'Account' AND depth = %(depth)s AND id <> %(account)s ORDER BY path LIMIT 1
