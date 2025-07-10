INSERT INTO denied_logins (
    type,
    username,
    from_ip,
    ip_country,
    ip_details,
    details,
    timestamp
) VALUES (
    :type,
    :username,
    :from_ip,
    :ip_country,
    :ip_details,
    :details,
    :timestamp
)
