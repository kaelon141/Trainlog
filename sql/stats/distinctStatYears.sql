SELECT DISTINCT 
    strftime('%Y', COALESCE(utc_start_datetime, start_datetime)) AS year
FROM trip
WHERE type = 'train'
AND strftime('%Y', COALESCE(utc_start_datetime, start_datetime)) > '1950'
AND (utc_start_datetime IS NOT NULL OR start_datetime NOT IN (1, -1))
AND (:username IS NULL OR username = :username)
ORDER BY year;