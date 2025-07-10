SELECT 
    strftime("%Y", start_datetime) AS year, 
    SUM(past) AS past, 
    SUM(plannedFuture) AS plannedFuture, 
    SUM(future) AS future
FROM counted
WHERE 
    strftime("%Y", start_datetime) NOT IN ('-471', '-4713') 
    AND (:username IS NULL OR username = :username)
    AND strftime("%Y", start_datetime) > '1950'
    AND strftime("%Y", start_datetime) < '2100'
GROUP BY year

UNION ALL

SELECT 
    'future' AS year, 
    0 AS past, 
    0 AS plannedFuture, 
    SUM(future) AS future
FROM counted
WHERE 
    start_datetime = 1
    AND (:username IS NULL OR username = :username)
GROUP BY start_datetime
HAVING SUM(future) > 0

ORDER BY year;