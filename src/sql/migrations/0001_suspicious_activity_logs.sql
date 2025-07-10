CREATE TABLE denied_logins (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL,
    type TEXT NOT NULL,
    from_ip TEXT NOT NULL,
    ip_country TEXT,
    ip_details TEXT,
    details TEXT,
    timestamp timestamp DEFAULT now()
);
