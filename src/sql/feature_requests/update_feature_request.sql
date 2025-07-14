UPDATE feature_requests 
SET title = :title, 
    description = :description, 
    last_modified = now()
WHERE id = :request_id;
