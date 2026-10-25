-- Q6 Circular payments: 3 to 8 transfers that start and end at the review account.
-- All events inside [start, end), strictly increasing in time, last - first <= 1800 s, Q5 amount rule
-- between neighbours, no 600 s gap rule. Stop at the first return (cur = review account is never extended);
-- other accounts may repeat. State: current account, ordered ids, first/last time, last amount, length.
WITH RECURSIVE cyc(cur, ids, first_t, last_t, last_amt, n) AS (
    SELECT t.receiver_id, ARRAY[t.transfer_id], t.occurred_at, t.occurred_at, t.amount_rwf, 1
    FROM transfers t
    WHERE t.sender_id = %(account)s AND t.occurred_at >= %(start)s AND t.occurred_at < %(end)s
  UNION ALL
    SELECT t.receiver_id, c.ids || t.transfer_id, c.first_t, t.occurred_at, t.amount_rwf, c.n + 1
    FROM cyc c JOIN transfers t ON t.sender_id = c.cur
    WHERE c.cur <> %(account)s AND c.n < 8
      AND t.occurred_at > c.last_t AND t.occurred_at < %(end)s AND t.occurred_at <= c.first_t + 1800
      AND 90::bigint * c.last_amt <= 100::bigint * t.amount_rwf
      AND 100::bigint * t.amount_rwf <= 105::bigint * c.last_amt
)
SELECT ids, n AS length FROM cyc WHERE cur = %(account)s AND n BETWEEN 3 AND 8 ORDER BY ids
