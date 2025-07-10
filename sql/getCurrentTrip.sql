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

SELECT uid
FROM UTC_Filtered 
WHERE username == :username
AND julianday('now') BETWEEN  julianday(utc_filtered_start_datetime) AND julianday(utc_filtered_end_datetime)
