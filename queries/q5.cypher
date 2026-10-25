// Q5 Rapid onward payments (same rules as q5.sql). Relationship uniqueness is automatic inside one MATCH.
MATCH (a:Account {account_id:$account})-[t1:TRANSFER]->(b:Account)-[t2:TRANSFER]->(c:Account)-[t3:TRANSFER]->(d:Account)
WHERE t1.occurred_at >= $start AND t1.occurred_at < $end
  AND t2.occurred_at >  t1.occurred_at AND t2.occurred_at <= t1.occurred_at + 600
  AND t3.occurred_at >  t2.occurred_at AND t3.occurred_at <= t2.occurred_at + 600
  AND 90 * t1.amount_rwf <= 100 * t2.amount_rwf AND 100 * t2.amount_rwf <= 105 * t1.amount_rwf
  AND 90 * t2.amount_rwf <= 100 * t3.amount_rwf AND 100 * t3.amount_rwf <= 105 * t2.amount_rwf
  AND a <> b AND a <> c AND a <> d AND b <> c AND b <> d AND c <> d
RETURN t1.transfer_id AS t1, t2.transfer_id AS t2, t3.transfer_id AS t3, d.account_id AS final_receiver
ORDER BY t1, t2, t3, final_receiver
