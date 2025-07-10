SELECT
    id,
    username,
    type,
    from_ip,
    ip_country,
    ip_details,
    details,
    timestamp
FROM denied_logins
ORDER BY timestamp DESC
