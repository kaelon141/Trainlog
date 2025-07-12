INSERT INTO feature_request_votes (feature_request_id, username, vote_type, created)
VALUES (:request_id, :username, :vote_type, now())
