import random
import time

import requests

TIMEOUT = (5, 30)   # (connect, read)
MAX_ATTEMPTS = 4    # retry budget for a single url
BASE_DELAY = 1      # in seconds; doubles each attempt
DELAY_CAP = 30      # maximum sleep time
TRANSIENT_STATUS = {429, 500, 502, 503, 504}


class PermanentError(Exception):
    """The answer of the sever won't change. Don't retry."""

class GaveUp(Exception):
    """Retried the allowed number of times and it still failed."""

def get_delay(attempt, retry_after=None):
    """Compute seconds to wait before attempt+1. Delay time increases exponentially, jitters, and is capped"""
    if retry_after is not None:
        return min(retry_after, DELAY_CAP)
    return min(BASE_DELAY * 2 ** (attempt - 1), DELAY_CAP) + random.uniform(0,1) 

def fetch_robust(url, params=None, attempts=MAX_ATTEMPTS, log=print):
    """GET url, retrying only what is worth retrying"""
    for attempt in range(1, attempts + 1):
        retry_after = None
        try:
            resp = requests.get(url, params, timeout=TIMEOUT)
        except (requests.ConnectionError, requests.Timeout) as exc:
            reason = type(exc).__name__
        else:
            if resp.status_code == 200:
                return resp
            if resp.status_code not in TRANSIENT_STATUS:
                raise PermanentError(f"HTTP {resp.status_code} for {resp.url}")
            reason = f"HTTP {resp.status_code}"
            if resp.headers.get("Retry-After", "").isdigit():
                    retry_after = int(resp.headers["Retry-After"]) 

        if attempt == attempts:
            raise GaveUp(f"{reason} after {attempt} attempts: {url}")
        wait = get_delay(attempt, retry_after)
        log(f"   {reason} - attempt {attempt}/{attempts}, retrying in {wait:.1f}s")
        time.sleep(wait)
