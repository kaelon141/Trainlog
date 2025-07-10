SELECT username, cc, percent
FROM percents
WHERE percent > 0 
AND cc {equals} 'world_squares'
AND username in ({usernames_placeholders})
ORDER BY cc, percent DESC