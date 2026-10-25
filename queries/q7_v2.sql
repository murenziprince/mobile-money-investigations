-- Q7 (version 2, improved) Shortest transfer connection - LENGTH ONLY, bidirectional search.
-- Search forward from the review account (depth <= ceil(bound/2)) and backward from the destination
-- along incoming transfers (depth <= floor(bound/2)); the shortest route of length L <= bound always has
-- a middle account at forward depth ceil(L/2) and backward depth floor(L/2), so
-- MIN(forward depth + backward depth) over common accounts is exactly the shortest length.
-- Two half-depth searches replace one full-depth search, avoiding the largest frontier levels.
-- Person-only restriction applied in both searches. NULL = no route within the bound.
WITH RECURSIVE fwd(acct, depth) AS (
    SELECT account_id, 0 FROM accounts WHERE account_id = %(account)s AND role = 'person'
  UNION
    SELECT t.receiver_id, f.depth + 1
    FROM fwd f
    JOIN transfers t ON t.sender_id = f.acct
    JOIN accounts a  ON a.account_id = t.receiver_id AND a.role = 'person'
    WHERE f.depth < (%(bound)s + 1) / 2
), bwd(acct, depth) AS (
    SELECT account_id, 0 FROM accounts WHERE account_id = %(destination)s AND role = 'person'
  UNION
    SELECT t.sender_id, b.depth + 1
    FROM bwd b
    JOIN transfers t ON t.receiver_id = b.acct
    JOIN accounts a  ON a.account_id = t.sender_id AND a.role = 'person'
    WHERE b.depth < %(bound)s / 2
)
SELECT MIN(f.depth + b.depth) AS length
FROM fwd f JOIN bwd b ON b.acct = f.acct
