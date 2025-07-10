import json
import logging
from datetime import datetime, timedelta

from py import utils
from src.pg import pg_session
from src.sql import suspicious_activity

logger = logging.getLogger(__name__)


def log_denied_login(
    type,
    username,
    details,
    from_ip,
):
    ip_data = utils.getIpDetails(from_ip)
    ip_country = ip_data["country"] if ip_data["country"] is not None else "UN"
    ip_details = json.dumps(ip_data)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    logger.warning(f'Failed login attempt for user "{username}": {type}')

    with pg_session() as pg:
        pg.execute(
            suspicious_activity.insert_denied_login(),
            {
                "type": type,
                "username": username,
                "from_ip": from_ip,
                "ip_country": ip_country,
                "ip_details": ip_details,
                "details": details,
                "timestamp": timestamp,
            },
        )


def check_denied_login(ip, username):
    one_hour_ago = datetime.now() - timedelta(hours=1)
    timestamp_str = one_hour_ago.strftime("%Y-%m-%d %H:%M:%S")

    with pg_session() as pg:
        # Check errors with the same username in the past hour
        username_errors = pg.execute(
            """
            SELECT COUNT(*) FROM denied_logins
            WHERE username = :username AND timestamp > :timestamp_str
            """,
            {
                "username": username,
                "timestamp_str": timestamp_str,
            },
        ).scalar()

        # Check errors with the same IP in the past hour
        ip_errors = pg.execute(
            """
            SELECT COUNT(*) FROM denied_logins
            WHERE from_ip = :ip AND timestamp > :timestamp_str
            """,
            {
                "ip": ip,
                "timestamp_str": timestamp_str,
            },
        ).scalar()

    if username_errors > 10 or ip_errors > 50:
        return False

    return True


def list_denied_logins():
    with pg_session() as pg:
        result = pg.execute(suspicious_activity.list_denied_logins()).fetchall()

    return result


def log_suspicious_activity(url, error_type, offending_part, from_ip, details=None):
    ip_data = utils.getIpDetails(from_ip)
    ip_country = ip_data["country"] if ip_data["country"] is not None else "UN"
    ip_details = json.dumps(ip_data)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    logger.info(
        f"Suspicious activity from {from_ip} ({ip_country}: {error_type}: {offending_part} ({url})"
    )

    with pg_session() as pg:
        pg.execute(
            suspicious_activity.insert_suspicious_activity(),
            {
                "url": url,
                "type": error_type,
                "offending_part": offending_part,
                "from_ip": from_ip,
                "ip_country": ip_country,
                "ip_details": ip_details,
                "details": details,
                "timestamp": timestamp,
            },
        )


def list_suspicious_activity(limit):
    with pg_session() as pg:
        result = pg.execute(
            suspicious_activity.list_suspicious_activity(), params={"limit": limit}
        ).fetchall()

    return result
