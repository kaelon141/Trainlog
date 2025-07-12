SELECT vote_type 
FROM feature_request_votes 
WHERE feature_request_id = :request_id AND username = :username
