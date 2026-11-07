"""MCP server: unofficial read-only access to mackolik.com live scores."""
from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from . import http as _http
from . import scores as _S

mcp = FastMCP("mackolik-mcp")

INSTRUCTIONS = """\
Unofficial read-only MCP server for mackolik.com, Türkiye's #1
sports-scores app. Data comes from the site's own JSON live feed
(vd.mackolik.com/livedata, ?group=0 for all of today or
?date=DD/MM/YYYY for one date) and its standings widget
(arsiv.mackolik.com/Home/StandingHandler.aspx?league=...) — no
login, no API key, no session cookies. Dates are DD/MM/YYYY in
the feed (the tools also accept ISO YYYY-MM-DD). Status codes:
0 = not started, 1/3/5 = live (minute like "81" or "IY"
half-time in status_text), 4 / "MS" = finished (Maç Sonu).
Odds are the site's 1/X/2 iddaa odds (display only, not betting
advice). Leagues: Tur (Türkiye), Eng, Esp, Ita, Ger for
standings; any league/country substring filter for scores.
Read-only; transport uses Chrome TLS impersonation; requests
are spaced ~0.8s apart. Built by Mohammad Abbasi
(mohammad-abbasi-sh) — Turkey MCP factory.\
"""


def _err(e: Exception) -> str:
    return json.dumps({"error": str(e)}, ensure_ascii=False)


def _validate_limit(limit: int, lo: int = 1, hi: int = 50) -> int:
    if not lo <= limit <= hi:
        raise ValueError(f"limit must be between {lo} and {hi}")
    return limit


def _feed(date: str | None) -> list[dict]:
    date_tr = _S.normalize_date(date)
    matches = _S.parse_livedata(_http.fetch_livedata_date(date_tr))
    # the feed is (almost) all the requested date, but can carry a
    # straggler from the next day — keep exactly the requested date
    matches = [m for m in matches if m["date"] == date_tr]
    return matches, date_tr


@mcp.tool()
def mackolik_live_scores(league: str | None = None, limit: int = 20) -> str:
    """Matches currently in play on mackolik.com (live minute,
    score, half-time, red cards, league, 1/X/2 odds). league:
    optional substring filter (e.g. "Süper Lig", "Premier Lig",
    "Türkiye"). limit 1..50."""
    try:
        _validate_limit(limit)
        matches = _S.parse_livedata(_http.fetch_livedata_group(0))
        live = _S.filter_matches(matches, status="live", league=league)
    except (ValueError, _http.MackolikError) as e:
        return _err(e)
    return json.dumps(
        {"count": min(limit, len(live)), "total_live": len(live),
         "matches": live[:limit]},
        ensure_ascii=False,
    )


@mcp.tool()
def mackolik_results(date: str | None = None, league: str | None = None,
                     limit: int = 20) -> str:
    """Finished matches for one date (default today). date:
    YYYY-MM-DD or DD/MM/YYYY. league: optional substring filter.
    limit 1..50."""
    try:
        _validate_limit(limit)
        matches, date_tr = _feed(date)
        done = _S.filter_matches(matches, status="finished", league=league)
    except (ValueError, _http.MackolikError) as e:
        return _err(e)
    return json.dumps(
        {"date": date_tr, "count": min(limit, len(done)),
         "total_finished": len(done), "matches": done[:limit]},
        ensure_ascii=False,
    )


@mcp.tool()
def mackolik_fixtures(date: str | None = None, league: str | None = None,
                      limit: int = 20) -> str:
    """Upcoming (not yet started) matches for one date (default
    today). date: YYYY-MM-DD or DD/MM/YYYY. league: optional
    substring filter. limit 1..50."""
    try:
        _validate_limit(limit)
        matches, date_tr = _feed(date)
        upcoming = _S.filter_matches(matches, status="upcoming", league=league)
    except (ValueError, _http.MackolikError) as e:
        return _err(e)
    return json.dumps(
        {"date": date_tr, "count": min(limit, len(upcoming)),
         "total_upcoming": len(upcoming), "matches": upcoming[:limit]},
        ensure_ascii=False,
    )


@mcp.tool()
def mackolik_standings(league: str = "Tur") -> str:
    """League standings. league: Tur (Türkiye Süper Lig), Eng
    (Premier Lig), Esp (LaLiga), Ita (Serie A) or Ger (Bundesliga).
    Returns rank, team, played, points, goal difference."""
    try:
        code = league.strip()
        if code not in _S.LEAGUES:
            raise ValueError(
                f"unknown league {league!r}: use one of {sorted(_S.LEAGUES)}"
            )
        rows = _S.parse_standings(_http.fetch_standings(code))
    except (ValueError, _http.MackolikError) as e:
        return _err(e)
    return json.dumps(
        {"league": code, "league_name": _S.LEAGUES[code],
         "count": len(rows), "standings": rows},
        ensure_ascii=False,
    )


@mcp.tool()
def mackolik_match_detail(match_id: int, date: str | None = None) -> str:
    """Full detail for one match by its mackolik match id (from the
    scores/results/fixtures tools). date: the match's date
    (YYYY-MM-DD or DD/MM/YYYY, default today) — the feed is
    per-day, so a past match needs its date. Returns teams,
    league, date/time, status, score, half-time, red cards,
    1/X/2 odds and the match page URL."""
    try:
        matches, date_tr = _feed(date)
        row = next((m for m in matches if m["match_id"] == match_id), None)
        if row is None:
            raise ValueError(
                f"match {match_id} not found in the {date_tr} feed — "
                "check the id and the date"
            )
    except (ValueError, _http.MackolikError) as e:
        return _err(e)
    return json.dumps({"date": date_tr, **row}, ensure_ascii=False)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
