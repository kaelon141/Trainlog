SELECT username, vote_type, created 
FROM feature_request_votes 
WHERE feature_request_id = :request_id
ORDER BY created DESC
