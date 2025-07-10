SELECT trip_id, path
FROM paths
WHERE trip_id IN ({trip_ids})