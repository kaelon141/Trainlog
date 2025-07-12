UPDATE feature_request_votes 
SET vote_type = :vote_type, created = now()
WHERE feature_request_id = :request_id AND username = :username
