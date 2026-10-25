-- Q7 (version 1, baseline) Shortest transfer connection - LENGTH ONLY.
-- Directed transfer neighbours over the full month, amounts and time order ignored. Every account on the
-- route (start, intermediates, destination) must have role person; the restriction is applied DURING the
-- search by joining to accounts at every step. NULL result = no route within the bound.
-- Weakness: UNION de-duplicates (account, depth) pairs, so an account reached at depth 2 is expanded again
-- at depths 3, 4 ... and every repeated payment is re-read. See plans/ for the wasted work.
WITH RECURSIVE reach(acct, depth) AS (
    SELECT account_id, 0 FROM accounts WHERE account_id = %(account)s AND role = 'person'
  UNION
    SELECT t.receiver_id, r.depth + 1
    FROM reach r
    JOIN transfers t ON t.sender_id = r.acct
    JOIN accounts a  ON a.account_id = t.receiver_id AND a.role = 'person'
    WHERE r.depth < %(bound)s
)
SELECT MIN(depth) AS length FROM reach WHERE acct = %(destination)s
