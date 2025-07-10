INSERT INTO suspicious_activity (
    url,
    type,
    offending_part,
    details,
    from_ip,
    ip_country,
    ip_details
) VALUES (
    :url,
    :type,
    :offending_part,
    :details,
    :from_ip,
    :ip_country,
    :ip_details
)
