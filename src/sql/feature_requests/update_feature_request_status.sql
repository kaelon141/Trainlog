UPDATE feature_requests 
SET status = :status, last_modified = now()
WHERE id = :request_id
