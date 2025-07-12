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
ORDER BY score DESC, created DESC;

-- src/sql/feature_requests/list_feature_requests_with_votes.sql
SELECT 
    fr.id,
    fr.title,
    fr.description,
    fr.username,
    fr.status,
    fr.created,
    fr.upvotes,
    fr.downvotes,
    fr.score,
    CASE 
        WHEN frv.vote_type = 'upvote' THEN 1
        WHEN frv.vote_type = 'downvote' THEN -1
        ELSE 0
    END as user_vote
FROM feature_requests fr
LEFT JOIN feature_request_votes frv ON fr.id = frv.feature_request_id 
    AND frv.username = :username
ORDER BY fr.score DESC, fr.created DESC;

-- src/sql/feature_requests/insert_feature_request.sql
INSERT INTO feature_requests (title, description, username, created, last_modified)
VALUES (:title, :description, :username, now(), now())
RETURNING id;

-- src/sql/feature_requests/update_feature_request_status.sql
UPDATE feature_requests 
SET status = :status, last_modified = now()
WHERE id = :request_id;

-- src/sql/feature_requests/get_user_vote.sql
SELECT vote_type 
FROM feature_request_votes 
WHERE feature_request_id = :request_id AND username = :username;

-- src/sql/feature_requests/insert_vote.sql
INSERT INTO feature_request_votes (feature_request_id, username, vote_type, created)
VALUES (:request_id, :username, :vote_type, now());

-- src/sql/feature_requests/update_vote.sql
UPDATE feature_request_votes 
SET vote_type = :vote_type, created = now()
WHERE feature_request_id = :request_id AND username = :username;

-- src/sql/feature_requests/delete_vote.sql
DELETE FROM feature_request_votes 
WHERE feature_request_id = :request_id AND username = :username;

-- src/sql/feature_requests/update_vote_counts.sql
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
WHERE id = :request_id;

-- src/sql/feature_requests/list_voters.sql
SELECT username, vote_type, created 
FROM feature_request_votes 
WHERE feature_request_id = :request_id
ORDER BY created DESC;