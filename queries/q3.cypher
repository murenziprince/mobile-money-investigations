// Q3 Shared devices. Cypher has no two-argument max/min, so CASE picks the later start / earlier end.
// u1.first_day <= u2.last_day AND u2.first_day <= u1.last_day  <=>  max(first) <= min(last).
MATCH (a:Account {account_id:$account})-[u1:USED_DEVICE]->(d:Device)<-[u2:USED_DEVICE]-(o:Account)
WHERE o <> a AND u1.first_day <= u2.last_day AND u2.first_day <= u1.last_day
RETURN o.account_id AS other_account, d.device_id AS device_id, d.access_type AS access_type,
       CASE WHEN u1.first_day > u2.first_day THEN u1.first_day ELSE u2.first_day END AS overlap_start,
       CASE WHEN u1.last_day  < u2.last_day  THEN u1.last_day  ELSE u2.last_day  END AS overlap_end
ORDER BY other_account, device_id
