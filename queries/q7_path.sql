-- Q7 supporting path (SQL): ONE shortest person-only route, as an ordered array of account ids.
-- Reuses the bidirectional search to find a meeting account on a shortest route, then rebuilds each half
-- with path-carrying searches limited to that half's depth. Returns no row when there is no route.
WITH RECURSIVE fwd(acct, depth) AS (
    SELECT account_id, 0 FROM accounts WHERE account_id = %(account)s AND role = 'person'
  UNION
    SELECT t.receiver_id, f.depth + 1
    FROM fwd f JOIN transfers t ON t.sender_id = f.acct
    JOIN accounts a ON a.account_id = t.receiver_id AND a.role = 'person'
    WHERE f.depth < (%(bound)s + 1) / 2
), bwd(acct, depth) AS (
    SELECT account_id, 0 FROM accounts WHERE account_id = %(destination)s AND role = 'person'
  UNION
    SELECT t.sender_id, b.depth + 1
    FROM bwd b JOIN transfers t ON t.receiver_id = b.acct
    JOIN accounts a ON a.account_id = t.sender_id AND a.role = 'person'
    WHERE b.depth < %(bound)s / 2
), meet AS (
    SELECT f.acct, f.depth AS fd, b.depth AS bd
    FROM fwd f JOIN bwd b ON b.acct = f.acct
    ORDER BY f.depth + b.depth, f.acct LIMIT 1
), fpath(acct, depth, path) AS (
    SELECT account_id, 0, ARRAY[account_id] FROM accounts WHERE account_id = %(account)s
  UNION ALL
    SELECT t.receiver_id, p.depth + 1, p.path || t.receiver_id
    FROM fpath p JOIN transfers t ON t.sender_id = p.acct
    JOIN accounts a ON a.account_id = t.receiver_id AND a.role = 'person'
    WHERE p.depth < (SELECT fd FROM meet)
), bpath(acct, depth, path) AS (
    SELECT account_id, 0, ARRAY[account_id] FROM accounts WHERE account_id = %(destination)s
  UNION ALL
    SELECT t.sender_id, p.depth + 1, t.sender_id || p.path
    FROM bpath p JOIN transfers t ON t.receiver_id = p.acct
    JOIN accounts a ON a.account_id = t.sender_id AND a.role = 'person'
    WHERE p.depth < (SELECT bd FROM meet)
)
SELECT fp.path || bp.path[2:] AS path
FROM meet m
JOIN fpath fp ON fp.acct = m.acct AND fp.depth = m.fd
JOIN bpath bp ON bp.acct = m.acct AND bp.depth = m.bd
ORDER BY 1 LIMIT 1
