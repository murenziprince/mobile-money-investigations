// Q4 Ownership and device network. Cypher cannot take a parameter as a path bound, so {depth} is
// substituted into the text (an int, never user text). DISTINCT directly after the pattern lets Neo4j use
// a pruning breadth-first expansion (look for PruningVarExpand in PROFILE) instead of enumerating every trail.
MATCH (a:Account {account_id:$account})
MATCH (a)-[:OWNS|USED_DEVICE*1..{depth}]-(b:Account)
WHERE b <> a
WITH DISTINCT b
MATCH (c:Customer)-[:OWNS]->(b)
RETURN c.region AS region, count(b) AS accounts
ORDER BY region
