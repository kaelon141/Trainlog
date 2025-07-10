SELECT json_array(MIN(origin_station, destination_station),MAX(origin_station, destination_station)) as 'route', sum(plannedFuture) as 'plannedFuture', sum(future) as 'future', sum(past) as "past", (sum(past) + sum(plannedFuture) + sum(future)) as 'count'
FROM counted
WHERE (:username IS NULL OR username = :username)
GROUP BY MIN(origin_station, destination_station), MAX(origin_station, destination_station)
order by count DESC
LIMIT 