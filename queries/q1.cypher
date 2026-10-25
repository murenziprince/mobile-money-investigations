// Q1 Account activity (same question as q1.sql). Aggregation without a grouping key always returns one row.
MATCH (a:Account {account_id:$account})-[t:TRANSFER]->()
WHERE t.occurred_at >= $start AND t.occurred_at < $end
RETURN count(t) AS outgoing_count, coalesce(sum(t.amount_rwf), 0) AS outgoing_rwf
