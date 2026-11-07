"""Parsing for mackolik.com's livedata JSON feed + standings widget.

Row layout decoded from the site's own livescore-go.js (verified
live 2026-11-07, fixture tests/fixtures/livedata-today.json):
- "m": array of match rows. [0] match id, [1] home team id,
  [2] home team, [3] away team id, [4] away team, [5] status code,
  [6] status text (minute "81'" / "MS" full-time / "IY" half-time /
  "" not started), [7] score "H-A" ("" if not started),
  [15] detail dict {h1, h2 (half-time), k1, k2 (red cards),
  goal, ogd, e}, [16] kick-off "HH:MM", [18]/[19]/[20] odds
  1/X/2 (verified against the detail page: 3.83/3.02/1.68),
  [35] date "DD/MM/YYYY", [36] group [countryId, country,
  groupId, league, seasonId, season, ...], [37] sport ("1"
  football, "2" basketball).
- "e": recently-updated matches feed (same shape, fewer fields);
  the "m" feed is the complete one and is what the tools use.
- Status codes (from the JS): 0 = not started; 1/3/5 = live
  (minute in [6]); 2/14-19 = status text in [6]; 4 = finished.

Standings widget (StandingHandler.aspx): <table
id="tblLightStanding"> rows: rank | team (link) | played |
points | goal difference ("Av").
"""
from __future__ import annotations

import html
import json
import re
from datetime import date
from zoneinfo import ZoneInfo

_TR_UPPER_TO_LOWER = str.maketrans({
    "İ": "i", "I": "ı", "Ş": "ş", "Ğ": "ğ",
    "Ü": "ü", "Ö": "ö", "Ç": "ç",
})

LEAGUES = {
    "Tur": "Türkiye",
    "Eng": "İngiltere",
    "Esp": "İspanya",
    "Ita": "İtalya",
    "Ger": "Almanya",
}


def _tr_lower(s: str) -> str:
    return s.translate(_TR_UPPER_TO_LOWER).lower()


def slugify(name: str) -> str:
    """Team/match name -> URL slug (Eyüpspor-Kocaelispor)."""
    s = _tr_lower((name or "").strip())
    s = re.sub(r"[ş]", "s", s)
    s = re.sub(r"[ğ]", "g", s)
    s = re.sub(r"[ü]", "u", s)
    s = re.sub(r"[ö]", "o", s)
    s = re.sub(r"[ç]", "c", s)
    s = re.sub(r"[ı]", "i", s)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    if not s:
        raise ValueError(f"cannot slugify {name!r}")
    return s


def today_tr() -> str:
    """Today's date in Türkiye time, DD/MM/YYYY (the feed's format)."""
    from datetime import datetime

    try:
        d = datetime.now(ZoneInfo("Europe/Istanbul")).date()
    except Exception:
        d = date.today()
    return f"{d.day:02d}/{d.month:02d}/{d.year}"


def normalize_date(value: str | None) -> str:
    """Accept YYYY-MM-DD or DD/MM/YYYY (or DD.MM.YYYY); return DD/MM/YYYY."""
    if not value:
        return today_tr()
    v = value.strip()
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", v)
    if m:
        return f"{m.group(3)}/{m.group(2)}/{m.group(1)}"
    m = re.fullmatch(r"(\d{2})[./](\d{2})[./](\d{4})", v)
    if m:
        return f"{m.group(1)}/{m.group(2)}/{m.group(3)}"
    raise ValueError(
        f"bad date {value!r}: use YYYY-MM-DD or DD/MM/YYYY"
    )


def _clean(text: str | None) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _status(code, text: str) -> str:
    """live | finished | upcoming | other.

    From the site's JS + the recorded feed: 0/12 = not started
    (empty status text); 1/3/5 = live (minute number in [6],
    e.g. "81" — the site adds the "'" when rendering); 14/15/17
    = basketball periods ("1P ", "2P ", "4P 8:34"); 20 = "UZ"
    (extra time); 4/13 with "MS" = finished (Maç Sonu);
    "IY" = half-time (live).
    """
    text = (text or "").strip()
    if text == "MS" or code in (4, 13):
        return "finished"
    if code in (0, 12):
        return "upcoming"
    if (code in (1, 3, 5, 14, 15, 16, 17, 18, 19, 20)
            or text in ("IY", "UZ") or text.endswith("'")):
        return "live"
    return "other"


def _parse_score(raw) -> tuple[int | None, int | None]:
    if not raw:
        return None, None
    m = re.fullmatch(r"(\d+)-(\d+)", str(raw).strip())
    if not m:
        return None, None
    return int(m.group(1)), int(m.group(2))


def parse_match(row: list) -> dict:
    """One livedata "m" row -> a match dict."""
    group = row[36] if len(row) > 36 and isinstance(row[36], list) else []
    detail = row[15] if len(row) > 15 and isinstance(row[15], dict) else {}
    home_goals, away_goals = _parse_score(row[7] if len(row) > 7 else "")
    code = row[5] if len(row) > 5 else 0
    text = row[6] if len(row) > 6 else ""
    status = _status(code, text)
    score = row[7] if len(row) > 7 else ""
    if status in ("live", "finished") and not score:
        # the feed leaves the score blank while no goal has been
        # scored — a live/finished match with no score is 0-0
        home_goals, away_goals, score = 0, 0, "0-0"
    return {
        "match_id": row[0],
        "home_team": row[2],
        "away_team": row[4],
        "league": group[3] if len(group) > 3 else "",
        "country": group[1] if len(group) > 1 else "",
        "season": group[5] if len(group) > 5 else "",
        "date": row[35] if len(row) > 35 else "",
        "time": row[16] if len(row) > 16 else "",
        "status": status,
        "status_text": text,
        "home_goals": home_goals,
        "away_goals": away_goals,
        "score": score,
        "half_time_home": detail.get("h1") or None,
        "half_time_away": detail.get("h2") or None,
        "red_cards_home": detail.get("k1") or None,
        "red_cards_away": detail.get("k2") or None,
        "odds_1": row[18] if len(row) > 18 else "",
        "odds_x": row[19] if len(row) > 19 else "",
        "odds_2": row[20] if len(row) > 20 else "",
        "sport": "basketball" if str(row[37]) == "2" else "football",
        "url": "https://arsiv.mackolik.com/Futbol-Mac/{}/{}".format(
            row[0], slugify(f"{row[2]}-{row[4]}")
        ),
    }


def parse_livedata(json_text: str) -> list[dict]:
    """Full livedata JSON -> list of match dicts."""
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"livedata feed is not valid JSON: {e}") from e
    rows = data.get("m") or []
    return [parse_match(r) for r in rows if isinstance(r, list) and len(r) > 36]


def filter_matches(matches: list[dict], status: str | None = None,
                   league: str | None = None) -> list[dict]:
    out = matches
    if status:
        out = [m for m in out if m["status"] == status]
    if league:
        needle = _tr_lower(league)
        out = [m for m in out
               if needle in _tr_lower(m["league"])
               or needle in _tr_lower(m["country"])]
    return out


def parse_standings(html_text: str) -> list[dict]:
    """StandingHandler widget table -> rows (rank, team, played, points, gd)."""
    rows: list[dict] = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", html_text, re.S):
        cells = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        if len(cells) != 5:
            continue
        rank = _clean(cells[0])
        if not rank.isdigit():
            continue
        team = _clean(cells[1])
        try:
            played, points, gd = (int(_clean(c)) for c in cells[2:5])
        except ValueError:
            continue
        rows.append({
            "rank": int(rank), "team": team, "played": played,
            "points": points, "goal_difference": gd,
        })
    return rows
