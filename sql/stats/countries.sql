SELECT countries, past, plannedFuture
FROM counted
WHERE (:username IS NULL OR username = :username) AND future = 0
