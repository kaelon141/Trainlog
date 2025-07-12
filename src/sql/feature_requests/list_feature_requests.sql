SELECT 
    id,
    title,
    description,
    username,
    status,
    created,
    upvotes,
    downvotes,
    score
FROM feature_requests
ORDER BY score DESC, created DESC
