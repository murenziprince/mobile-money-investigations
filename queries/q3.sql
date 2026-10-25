-- Q3 Shared devices: other accounts observed on the same device in an overlapping day interval.
-- Overlap holds when max(first_day) <= min(last_day). Both handsets and public terminals included.
SELECT o.account_id AS other_account, a.device_id, d.access_type,
       GREATEST(a.first_day, o.first_day) AS overlap_start,
       LEAST(a.last_day, o.last_day)      AS overlap_end
FROM account_devices a
JOIN account_devices o ON o.device_id = a.device_id AND o.account_id <> a.account_id
JOIN devices d ON d.device_id = a.device_id
WHERE a.account_id = %(account)s
  AND GREATEST(a.first_day, o.first_day) <= LEAST(a.last_day, o.last_day)
ORDER BY o.account_id, a.device_id
