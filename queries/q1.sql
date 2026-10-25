-- Q1 Account activity: outgoing count and total RWF in the hour [start, end), all receiver roles.
-- start/end are epoch seconds computed in Python from 09:45:00 inclusive to 10:45:00 exclusive CAT.
SELECT COUNT(*) AS outgoing_count, COALESCE(SUM(amount_rwf), 0) AS outgoing_rwf
FROM transfers
WHERE sender_id = %(account)s
  AND occurred_at >= %(start)s AND occurred_at < %(end)s
