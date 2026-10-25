-- Q5 Rapid onward payments: exactly three directed transfers through four distinct accounts.
-- t1 starts at the review account inside the hour; each later transfer is strictly later than the
-- previous one and at most 600 s after it (it may fall outside the hour). Amount rule, in BIGINT:
-- 90*previous <= 100*next <= 105*previous.
SELECT t1.transfer_id AS t1, t2.transfer_id AS t2, t3.transfer_id AS t3, t3.receiver_id AS final_receiver
FROM transfers t1
JOIN transfers t2 ON t2.sender_id = t1.receiver_id
JOIN transfers t3 ON t3.sender_id = t2.receiver_id
WHERE t1.sender_id = %(account)s
  AND t1.occurred_at >= %(start)s AND t1.occurred_at < %(end)s
  AND t2.occurred_at >  t1.occurred_at AND t2.occurred_at <= t1.occurred_at + 600
  AND t3.occurred_at >  t2.occurred_at AND t3.occurred_at <= t2.occurred_at + 600
  AND 90::bigint * t1.amount_rwf <= 100::bigint * t2.amount_rwf
  AND 100::bigint * t2.amount_rwf <= 105::bigint * t1.amount_rwf
  AND 90::bigint * t2.amount_rwf <= 100::bigint * t3.amount_rwf
  AND 100::bigint * t3.amount_rwf <= 105::bigint * t2.amount_rwf
  AND t1.sender_id <> t1.receiver_id AND t1.sender_id <> t2.receiver_id AND t1.sender_id <> t3.receiver_id
  AND t1.receiver_id <> t2.receiver_id AND t1.receiver_id <> t3.receiver_id
  AND t2.receiver_id <> t3.receiver_id
ORDER BY t1.transfer_id, t2.transfer_id, t3.transfer_id, t3.receiver_id
