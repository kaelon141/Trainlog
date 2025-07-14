SELECT id, title, description, username
FROM feature_requests
WHERE id = :request_id;