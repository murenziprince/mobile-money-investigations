-- Q2 Daily activity over the full month, grouped by Africa/Kigali (CAT) calendar day.
SELECT (to_timestamp(occurred_at) AT TIME ZONE 'Africa/Kigali')::date AS day,
       COUNT(*) AS transfer_count, SUM(amount_rwf) AS total_rwf
FROM transfers
GROUP BY 1
ORDER BY 1
