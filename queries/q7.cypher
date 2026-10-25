// Q7 Shortest transfer connection - LENGTH ONLY, native shortest path. {bound} is substituted into the text
// (Cypher cannot parameterize a path bound). The all(...) predicate over nodes(p) is evaluated while the
// breadth-first search runs, so a non-person account is never used to reach the destination.
// No row = no route within the bound.
MATCH (a:Account {account_id:$account}), (b:Account {account_id:$destination})
MATCH p = shortestPath((a)-[:TRANSFER*..{bound}]->(b))
WHERE all(n IN nodes(p) WHERE n.role = 'person')
RETURN length(p) AS length
// Neo4j >= 5.21 alternative with quantified path patterns (role tested on every node during the search):
// MATCH p = SHORTEST 1 (a)((:Account {role:'person'})-[:TRANSFER]->()){1,{bound}}(b)
// WHERE b.role = 'person' AND a.role = 'person'
