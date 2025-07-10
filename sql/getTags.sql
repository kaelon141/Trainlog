SELECT 
    tags.uuid, 
    tags.uid, 
    tags.name,
    tags.colour,
    GROUP_CONCAT(tags_associations.trip_id) as trip_ids
FROM tags
LEFT JOIN tags_associations ON tags.uid = tags_associations.tag_id
WHERE tags.username = ?
GROUP BY tags.uid