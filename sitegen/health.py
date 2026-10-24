"""Public up-or-down checks for sites Nathan runs, shown on the front page.

Runs every hour from the GitHub job and writes .cache/health.json (not
committed). It only loads each site's public home page, the same as any
visitor would: no keys, no private data.
"""

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / ".cache" / "health.json"
USER_AGENT = "Mozilla/5.0 (compatible; nathanjmetz-status/1.0; +https://nathanjmetz.github.io)"

SITES = [
    {"name": "Brawn", "source": "Brawn", "url": "https://gobrawn.com"},
]

SLOW_MS = 3000  # slower than this reads as "slow"


def check(site, get=None, clock=time.monotonic):
    """One site's status: up, slow or down, with the HTTP code and response time."""
    get = get or (lambda url: requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=20))
    started = clock()
    try:
        resp = get(site["url"])
        ms = round((clock() - started) * 1000)
        code = resp.status_code
        if code >= 400:
            state = "down"
        elif ms > SLOW_MS:
            state = "slow"
        else:
            state = "up"
        return {**site, "state": state, "code": code, "ms": ms}
    except requests.RequestException as exc:
        return {**site, "state": "down", "code": None, "ms": None, "error": type(exc).__name__}


def run(now=None, get=None):
    now = now or datetime.now(timezone.utc)
    return {"checked": now.isoformat(), "sites": [check(s, get) for s in SITES]}


def load(path=OUT):
    """The last check, or None when there isn't one (local builds, pull requests)."""
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def main():
    result = run()
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(result, indent=1) + "\n")
    for s in result["sites"]:
        print(f"{s['name']}: {s['state']} ({s['code']}, {s['ms']} ms)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
