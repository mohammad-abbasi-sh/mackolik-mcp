"""HTTP layer for mackolik_mcp.

mackolik.com redirects to arsiv.mackolik.com (Akamai-fronted, no
bot wall — plain 200). The live-scores data comes from the site's
own JSON feed, vd.mackolik.com/livedata, which the site's JS
(livescore-go.js) calls with ?group=<id> (0 = all) or
?date=DD/MM/YYYY — no login, no API key. Standings come from the
site's own handler, arsiv.mackolik.com/Home/StandingHandler.aspx
?league=Tur|Eng|Esp|Ita|Ger (the homepage standings widget calls
exactly this). The transport uses curl-cffi chrome120
impersonation, the same proven pattern as the other
Turkey-factory servers. Requests are kept gentle (one at a time,
~0.8s apart) and read-only.

Verified live 2026-11-07: livedata?group=0 -> 288KB JSON, 836
matches for the day; livedata?date=07/11/2026 -> 471KB JSON;
StandingHandler Tur -> 10-row Süper Lig table.
"""
from __future__ import annotations

import time
from urllib.parse import quote

from curl_cffi import requests as _r

VD_BASE = "https://vd.mackolik.com/livedata"
ARSIV_BASE = "https://arsiv.mackolik.com"
TIMEOUT = 30.0
MIN_INTERVAL = 0.8  # seconds between requests — be polite

_HEADERS = {
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
    "Accept": "application/json, text/html, */*",
    "Referer": "https://arsiv.mackolik.com/Canli-Sonuclar",
}

_last_fetch = 0.0


class MackolikError(RuntimeError):
    pass


def _get(url: str) -> str:
    global _last_fetch
    wait = MIN_INTERVAL - (time.monotonic() - _last_fetch)
    if wait > 0:
        time.sleep(wait)
    try:
        resp = _r.get(url, impersonate="chrome120", headers=_HEADERS, timeout=TIMEOUT)
    except Exception as e:
        raise MackolikError(f"network error fetching {url}: {e}") from e
    finally:
        _last_fetch = time.monotonic()
    if resp.status_code == 403:
        raise MackolikError(
            "mackolik.com refused the request (HTTP 403, bot wall) — try again later"
        )
    if resp.status_code == 429:
        raise MackolikError(
            "mackolik.com rate-limited the request (HTTP 429) — try again later"
        )
    if resp.status_code == 404:
        raise MackolikError(f"page not found (HTTP 404): {url}")
    if resp.status_code != 200:
        raise MackolikError(f"unexpected HTTP {resp.status_code} fetching {url}")
    return resp.text


def fetch_livedata_group(group: int = 0) -> str:
    """Live feed for a group (0 = all matches, live + today)."""
    return _get(f"{VD_BASE}?group={group}")


def fetch_livedata_date(date_tr: str) -> str:
    """Live feed for one date, DD/MM/YYYY (the site's own format)."""
    return _get(f"{VD_BASE}?date={quote(date_tr, safe='')}")


def fetch_standings(league: str) -> str:
    """Standings widget HTML for Tur|Eng|Esp|Ita|Ger."""
    return _get(f"{ARSIV_BASE}/Home/StandingHandler.aspx?league={quote(league)}")
