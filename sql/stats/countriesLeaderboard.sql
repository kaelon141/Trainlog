
WITH UTC_Filtered AS (
	SELECT *,
		CASE
			WHEN utc_start_datetime IS NOT NULL
			THEN utc_start_datetime
			ELSE start_datetime 
		END AS utc_filtered_start_datetime
	FROM trip
), counted AS (SELECT *, 
CASE
	WHEN  (julianday('now') > julianday(utc_filtered_start_datetime) 
	OR utc_filtered_start_datetime = -1)
	AND utc_filtered_start_datetime != 1
	THEN 1
	ELSE 0
END AS 'past',
CASE
	WHEN  julianday('now') <= julianday(utc_filtered_start_datetime)
	THEN 1
	ELSE 0 
END AS 'plannedFuture',
CASE
	WHEN  utc_filtered_start_datetime=1
	THEN 1
	ELSE 0 
END AS 'future'
from UTC_Filtered)

SELECT username, countries FROM counted WHERE username IN ({}) AND past = 1