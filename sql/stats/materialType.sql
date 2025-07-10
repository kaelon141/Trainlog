SELECT 
    CASE 
        WHEN :tripType IN ('air', 'helicopter') AND a.iata IS NOT NULL THEN a.manufacturer || ' ' || a.model
        ELSE c.material_type
    END AS material,
    SUM(c.past) AS past,
    SUM(c.plannedFuture) AS plannedFuture,
    (SUM(c.past) + SUM(c.plannedFuture)) AS count
FROM 
    counted c
LEFT JOIN 
    airliners a ON c.material_type = a.iata
WHERE 
    (:username IS NULL OR c.username = :username)
    AND c.future = 0
    AND c.material_type IS NOT NULL
    AND c.material_type != ''
GROUP BY 
    CASE 
        WHEN :tripType IN ('air', 'helicopter') AND a.iata IS NOT NULL THEN a.manufacturer || ' ' || a.model
        ELSE c.material_type
    END
ORDER BY 
    count DESC;
