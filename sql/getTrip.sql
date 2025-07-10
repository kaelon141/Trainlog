WITH UTC_Filtered AS (
    SELECT *, 
    CASE
        WHEN utc_start_datetime IS NOT NULL
        THEN utc_start_datetime
        ELSE start_datetime 
    END AS 'utc_filtered_start_datetime',
    CASE
        WHEN utc_end_datetime IS NOT NULL
        THEN utc_end_datetime
        ELSE end_datetime 
    END AS 'utc_filtered_end_datetime'
    FROM trip
)

SELECT 
    t.*,
    CASE
        WHEN julianday('now') > julianday(utc_filtered_end_datetime) 
            OR utc_filtered_start_datetime = -1
            AND utc_filtered_start_datetime != 1
        THEN 'past'
        WHEN julianday('now') <= julianday(utc_filtered_start_datetime)
        THEN 'plannedFuture'
        WHEN julianday('now') BETWEEN  julianday(utc_filtered_start_datetime) AND julianday(utc_filtered_end_datetime)
        THEN 'current'
        WHEN utc_filtered_start_datetime = 1
        THEN 'future'
    END AS 'time',
    o.short_name AS operator_name,
    CASE
        -- Fetch the oldest logo if trip date is -1
        WHEN utc_filtered_start_datetime = -1 THEN (
            SELECT l.logo_url
            FROM operator_logos l
            WHERE l.operator_id = o.uid
            ORDER BY l.effective_date ASC
            LIMIT 1
        )
        -- Fetch the latest logo if trip date is 1
        WHEN utc_filtered_start_datetime = 1 THEN (
            SELECT l.logo_url
            FROM operator_logos l
            WHERE l.operator_id = o.uid
            ORDER BY l.effective_date DESC
            LIMIT 1
        )
        -- Fetch the logo closest to the trip start date
        ELSE (
            SELECT l.logo_url
            FROM operator_logos l
            WHERE l.operator_id = o.uid
              AND (l.effective_date <= t.utc_filtered_start_datetime OR l.effective_date IS NULL)
            ORDER BY l.effective_date DESC
            LIMIT 1
        )
    END AS logo_url
FROM UTC_Filtered t
LEFT JOIN operators o ON t.operator = o.short_name
WHERE t.uid = :trip_id;
