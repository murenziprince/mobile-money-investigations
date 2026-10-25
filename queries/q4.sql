-- Q4 Ownership and device network: distinct OTHER accounts within %(depth)s links, by owner region.
-- Node identity is (kind, id) so Customer 7 differs from Account 7. Every stored arrow is followed both ways.
-- walk uses UNION (not UNION ALL) so identical (kind, id, depth) states are expanded once per depth.
WITH RECURSIVE edges(sk, si, dk, di) AS (
    SELECT 'Customer', customer_id, 'Account',  account_id  FROM accounts
    UNION ALL SELECT 'Account',  account_id,  'Customer', customer_id FROM accounts
    UNION ALL SELECT 'Account',  account_id,  'Device',   device_id   FROM account_devices
    UNION ALL SELECT 'Device',   device_id,   'Account',  account_id  FROM account_devices
), walk(kind, id, depth) AS (
    SELECT 'Account', %(account)s::integer, 0
    UNION
    SELECT e.dk, e.di, w.depth + 1
    FROM walk w JOIN edges e ON e.sk = w.kind AND e.si = w.id
    WHERE w.depth < %(depth)s
)
SELECT c.region, COUNT(DISTINCT w.id) AS accounts
FROM walk w
JOIN accounts a  ON w.kind = 'Account' AND a.account_id = w.id
JOIN customers c ON c.customer_id = a.customer_id
WHERE w.id <> %(account)s
GROUP BY c.region
ORDER BY c.region
