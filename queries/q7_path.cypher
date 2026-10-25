// Q7 supporting path: ONE shortest person-only route with its account ids and transfer ids.
MATCH (a:Account {account_id:$account}), (b:Account {account_id:$destination})
MATCH p = shortestPath((a)-[:TRANSFER*..{bound}]->(b))
WHERE all(n IN nodes(p) WHERE n.role = 'person')
RETURN [n IN nodes(p) | n.account_id] AS accounts, [r IN relationships(p) | r.transfer_id] AS transfers
LIMIT 1
