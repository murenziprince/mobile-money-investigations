// Q4 supporting path (Cypher): one path of exactly {depth} links to another account, nodes typed by label.
MATCH p = (a:Account {account_id:$account})-[:OWNS|USED_DEVICE*{depth}]-(b:Account)
WHERE b <> a
RETURN [n IN nodes(p) | labels(n)[0] + ':' + toString(coalesce(n.customer_id, n.account_id, n.device_id))] AS path
ORDER BY path LIMIT 1
