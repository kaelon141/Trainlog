SELECT username, count(*) as 'trips' , sum(trip_length) as 'length', max(last_modified) as 'last_modified'
FROM trip
GROUP BY username