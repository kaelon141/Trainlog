SELECT tickets.uid, tickets.name, tickets.price, tickets.currency, tickets.purchasing_date, COUNT(trip.ticket_id) AS trip_count
FROM tickets
LEFT JOIN trip ON tickets.uid = trip.ticket_id
WHERE tickets.uid = ?
GROUP BY tickets.uid;
