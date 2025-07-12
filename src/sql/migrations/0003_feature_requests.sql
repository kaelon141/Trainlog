-- Feature Requests table
CREATE TABLE feature_requests (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    username TEXT NOT NULL,
    status TEXT DEFAULT 'open' CHECK (status IN ('open', 'working_on_it', 'completed', 'not_doing')),
    created TIMESTAMP DEFAULT now(),
    last_modified TIMESTAMP DEFAULT now(),
    upvotes INTEGER DEFAULT 0,
    downvotes INTEGER DEFAULT 0,
    score INTEGER DEFAULT 0
);

-- Feature Request Votes table
CREATE TABLE feature_request_votes (
    id SERIAL PRIMARY KEY,
    feature_request_id INTEGER NOT NULL,
    username TEXT NOT NULL,
    vote_type TEXT NOT NULL CHECK (vote_type IN ('upvote', 'downvote')),
    created TIMESTAMP DEFAULT now(),
    FOREIGN KEY (feature_request_id) REFERENCES feature_requests(id) ON DELETE CASCADE,
    UNIQUE(feature_request_id, username)
);