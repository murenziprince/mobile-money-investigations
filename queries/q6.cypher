// Q6 Circular payments. The path closes on the bound account `a`. The first all(...) filters every
// relationship to the hour so Neo4j can prune during expansion; the second applies ordering, the amount rule.
// none(...) enforces "stop at the first return" (no intermediate node is the review account).
MATCH p = (a:Account {account_id:$account})-[ts:TRANSFER*3..8]->(a)
WHERE all(r IN ts WHERE r.occurred_at >= $start AND r.occurred_at < $end)
  AND none(n IN nodes(p)[1..-1] WHERE n = a)
  AND ts[size(ts)-1].occurred_at - ts[0].occurred_at <= 1800
  AND all(i IN range(0, size(ts) - 2) WHERE
        ts[i].occurred_at < ts[i+1].occurred_at
        AND 90 * ts[i].amount_rwf <= 100 * ts[i+1].amount_rwf
        AND 100 * ts[i+1].amount_rwf <= 105 * ts[i].amount_rwf)
RETURN [r IN ts | r.transfer_id] AS ids, size(ts) AS length
ORDER BY ids
