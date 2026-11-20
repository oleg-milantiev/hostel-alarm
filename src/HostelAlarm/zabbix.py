"""Zabbix API client."""

import json
import logging
import urllib.request

logger = logging.getLogger("HostelAlarm.zabbix")


def fetch_stars(url):
    """Fetch stars_count_0 from Zabbix API."""
    logger.debug("Fetching from %s", url)
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "HostelAlarm/1.0")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
            data = json.loads(raw.decode("utf-8"))
        stars = data.get("stars_count_0")
        logger.debug("stars_count_0 = %s", stars)
        return stars
    except Exception as e:
        logger.exception("Failed to fetch stars from %s", url)
        return None
