, unique_stations AS (
	SELECT origin_station as 'station', * 
	FROM counted 
	UNION 
	SELECT destination_station as 'station', * 
	FROM counted 
)

SELECT station, sum(past) as 'past', sum(plannedFuture) as 'plannedFuture', (sum(past) + sum(plannedFuture) + sum(future)) as 'count'
FROM unique_stations
WHERE (:username IS NULL OR username = :username)
GROUP BY station
order by count DESC
LIMIT 
