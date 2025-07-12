INSERT INTO feature_requests (title, description, username, created, last_modified)
VALUES (:title, :description, :username, now(), now())
RETURNING id
