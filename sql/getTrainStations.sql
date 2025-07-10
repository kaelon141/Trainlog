SELECT * FROM train_stations 
WHERE 
    name LIKE :searchPatternAnywhere 
    OR latin_name LIKE :searchPatternAnywhere 
    OR city LIKE :searchPatternAnywhere 
    OR latin_city LIKE :searchPatternAnywhere 
    OR processed_name LIKE :searchPatternAnywhere
ORDER BY 
    CASE 
        WHEN processed_name LIKE :searchPatternStart THEN 1
        WHEN processed_name LIKE :searchPatternAnywhere THEN 2
        WHEN name LIKE :searchPatternStart THEN 3
        WHEN name LIKE :searchPatternAnywhere THEN 4
        WHEN latin_city LIKE :searchPatternStart THEN 5
        WHEN latin_city LIKE :searchPatternAnywhere THEN 6
        WHEN city LIKE :searchPatternStart THEN 7
        WHEN city LIKE :searchPatternAnywhere THEN 8
        ELSE 10
    END
LIMIT 10
