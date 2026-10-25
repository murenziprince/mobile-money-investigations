// Q2 Daily activity over the full month, grouped by Africa/Kigali (CAT) calendar day.
MATCH ()-[t:TRANSFER]->()
WITH date(datetime({epochSeconds: t.occurred_at, timezone: 'Africa/Kigali'})) AS day, t
RETURN toString(day) AS day, count(t) AS transfer_count, sum(t.amount_rwf) AS total_rwf
ORDER BY day
