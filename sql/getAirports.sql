SELECT * FROM airports 
WHERE 
    iata LIKE :searchPattern 
    OR name LIKE :searchPattern 
    OR ident LIKE :searchPattern 
    OR city LIKE :searchPattern 
ORDER BY iata LIKE :searchPattern DESC, ident LIKE :searchPattern DESC
LIMIT 10