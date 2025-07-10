SELECT uid 
FROM trip 
WHERE 
    origin_station = :orig 
    AND destination_station = :dest
    AND start_datetime = :start_datetime
    AND end_datetime = :end_datetime
    AND username = :username