CREATE TABLE IF NOT EXISTS paths (
        uid INTEGER NOT NULL, 
        trip_id INTEGER NOT NULL,
        path TEXT NOT NULL,
        PRIMARY KEY (uid)
    )