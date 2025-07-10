SELECT 
    tickets.uid, 
    tickets.name, 
    tickets.price, 
    tickets.currency, 
    tickets.purchasing_date,
    tickets.notes,
    tickets.active,
    tickets.active_countries,
    COUNT(trip.ticket_id) AS trip_count,
    tickets.price / COUNT(trip.ticket_id) as price_per_trip,
    tickets.price / SUM(trip.trip_length/1000) as price_per_km,
    GROUP_CONCAT(trip.uid) as trip_ids
FROM tickets
LEFT JOIN trip ON tickets.uid = trip.ticket_id
WHERE tickets.username = ?
GROUP BY tickets.uid
ORDER BY tickets.purchasing_date DESC;