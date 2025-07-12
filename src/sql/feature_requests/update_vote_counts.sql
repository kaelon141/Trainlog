UPDATE feature_requests
SET 
    upvotes = (
        SELECT COUNT(*) 
        FROM feature_request_votes 
        WHERE feature_request_id = :request_id AND vote_type = 'upvote'
    ),
    downvotes = (
        SELECT COUNT(*) 
        FROM feature_request_votes 
        WHERE feature_request_id = :request_id AND vote_type = 'downvote'
    ),
    score = (
        SELECT COUNT(CASE WHEN vote_type = 'upvote' THEN 1 END) - 
               COUNT(CASE WHEN vote_type = 'downvote' THEN 1 END)
        FROM feature_request_votes 
        WHERE feature_request_id = :request_id
    )
WHERE id = :request_id
