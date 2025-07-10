import random
import time

from flask import g, request, session

from py.flask_matomo import Matomo
from py.utils import getIp


class CustomMatomo(Matomo):
    """A custom Matomo class that overrides the before_request method to include the client's IP address."""

    def before_request(self):
        """Executed before every request, parses details about request"""
        # Don't track track request, if user used ignore() decorator for route
        url_rule = str(request.url_rule)
        if url_rule in self.ignored_routes:
            return
        if any(
            ua_pattern.match(str(request.user_agent))
            for ua_pattern in self.ignored_ua_patterns
        ):
            return
        if any(pattern.match(url_rule) for pattern in self.ignored_patterns):
            return

        url = self.base_url + request.path if self.base_url else request.url
        # action_name = request.url_rule
        action_name = request.endpoint
        user_agent = request.user_agent
        ip_address = getIp(request)
        if ip_address in ("127.0.0.1"):
            return

        data = {
            # site data
            "idsite": str(self.id_site),
            "rec": "1",
            "apiv": "1",
            "send_image": "0",
            # request data
            "ua": user_agent,
            "action_name": action_name,
            "url": url,
            "uid": session.get("logged_in", "public"),
            "cvar": {
                "http_status_code": None,
                "http_method": str(request.method),
            },
            "urlref": request.headers.get("Referer"),
            # random data
            "rand": random.getrandbits(32),
        }
        if self.token_auth:
            data["token_auth"] = self.token_auth
            data["cip"] = ip_address

        if request.accept_languages:
            data["lang"] = request.accept_languages[0][0]

        # Overwrite action_name, if it was configured with details()
        if self.routes_details.get(action_name) and self.routes_details.get(
            action_name, {}
        ).get("action_name"):
            data["action_name"] = self.routes_details.get(action_name, {}).get(
                "action_name"
            )

        g.flask_matomo2 = {
            "tracking": True,
            "start_ns": time.perf_counter_ns(),
            "tracking_data": data,
        }
