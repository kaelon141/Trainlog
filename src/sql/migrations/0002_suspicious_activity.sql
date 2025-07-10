CREATE TABLE suspicious_activity (
    id SERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    type TEXT NOT NULL,
    offending_part TEXT NOT NULL,
    from_ip TEXT NOT NULL,
    ip_country TEXT,
    ip_details TEXT,
    details TEXT,
    timestamp timestamp DEFAULT now()
);
