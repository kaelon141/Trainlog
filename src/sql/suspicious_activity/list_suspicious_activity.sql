SELECT
    id,
    url,
    type,
    offending_part,
    timestamp,
    details,
    from_ip,
    ip_country,
    ip_details
FROM suspicious_activity
ORDER BY timestamp DESC
{% if limit %}
    LIMIT :limit
{% endif %}
