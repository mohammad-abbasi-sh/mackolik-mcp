# mackolik-mcp 🇹🇷

> ⚠️ **Status: DEGRADED (2026-11-12)** — mackolik.com currently blocks automated access (HTTP 403) from this environment. All tools return a clear "blocked" error until the site allows access again. Check `mackolik_health` for the live status.


mcp-name: io.github.mohammad-abbasi-sh/mackolik-mcp

Unofficial **read-only** MCP server for mackolik.com, Türkiye's #1 sports-scores app (~38M installs) — live scores, results, fixtures, league standings and match detail for football (and basketball) worldwide, with Turkish leagues first-class.

> Built by Mohammad Abbasi as part of the "Turkey MCP factory" (Sepehr-style pipeline). Not affiliated with mackolik.com. Built for Mackolik only — never Sahadan (same owner, same underlying data).

## For AI agents

Add to your MCP client config (stdio):

```json
{
  "mcpServers": {
    "mackolik": {
      "command": "uvx",
      "args": ["mackolik-mcp==0.1.0"]
    }
  }
}
```

Or run locally: `python -m mackolik_mcp.server` (needs `mcp<2`, `curl-cffi`).

## Tools

| Tool | Description |
|------|-------------|
| `mackolik_live_scores` | Matches currently in play — `league` optional substring filter (e.g. "Süper Lig", "Premier Lig"), `limit` 1..50; minute, score, half-time, red cards, 1/X/2 odds |
| `mackolik_results` | Finished matches for one date (default today) — `date` YYYY-MM-DD or DD/MM/YYYY, `league` filter, `limit` 1..50 |
| `mackolik_fixtures` | Upcoming matches for one date (default today) — same params as results |
| `mackolik_standings` | League standings — `league`: Tur (Türkiye Süper Lig), Eng (Premier Lig), Esp (LaLiga), Ita (Serie A), Ger (Bundesliga); rank, team, played, points, goal difference |
| `mackolik_match_detail` | Full detail for one match by `match_id` (from the other tools) + optional `date` (the feed is per-day, so a past match needs its date) |

Example output (`mackolik_live_scores` / 2026-11-07):

```json
{"total_live": 34, "matches": [
  {"match_id": 4542744, "home_team": "Eyüpspor", "away_team": "Kocaelispor",
   "league": "Süper Lig", "country": "Türkiye", "date": "07/11/2026",
   "time": "13:30", "status": "live", "status_text": "17",
   "score": "0-0", "odds_1": "3.46", "odds_x": "2.97", "odds_2": "1.78",
   "url": "https://arsiv.mackolik.com/Futbol-Mac/4542744/eyupspor-kocaelispor"}, …]}
```

Example output (`mackolik_standings` / Tur):

```json
{"league": "Tur", "league_name": "Türkiye", "count": 9, "standings": [
  {"rank": 1, "team": "Galatasaray", "played": 10, "points": 25,
   "goal_difference": 11}, …]}
```

## How it works

mackolik.com redirects to arsiv.mackolik.com (Akamai-fronted, no bot wall). The live data comes from the site's own JSON feed, `vd.mackolik.com/livedata`, which the site's JavaScript calls with `?group=0` (all of today, 836 matches on 2026-11-07) or `?date=DD/MM/YYYY` (1,370 matches for 07/11/2026) — no login, no API key. Match rows are arrays decoded against the site's own `livescore-go.js`: id, teams, status code, status text, score, half-time/red-card detail, kick-off time, 1/X/2 iddaa odds (display only), date, and league group (country, league, season). Status codes: 0/12 = not started, 1/3/5 = live (minute number in status_text — the site adds the `'` when rendering), 14/15/17 = basketball periods, 20 = extra time ("UZ"), 4/13 with "MS" = finished (Maç Sonu). A live/finished match with a blank score field is 0-0 (no goal scored yet). Standings come from the site's own widget handler (`Home/StandingHandler.aspx?league=Tur|Eng|Esp|Ita|Ger`). Transport uses Chrome TLS impersonation (`curl-cffi`, `chrome120`); requests are spaced ~0.8s apart; everything is read-only. Note: "Süper Lig" is also the league name in Greece, Switzerland, Serbia, Slovakia, India and Indonesia — filter by country via the league substring or check the `country` field.

## Install

```bash
uvx mackolik-mcp==0.1.0        # run directly (needs uv)
# or
pip install mackolik-mcp==0.1.0
mackolik-mcp    # starts the MCP server on stdio
```

## Tests

```bash
python -m venv .venv && .venv/bin/pip install -e .
.venv/bin/python -m unittest discover -s tests -v
```

Offline tests run on recorded fixtures (real feed responses from 2026-11-07); live tests hit mackolik.com. 26/26 green at build time (14 offline + 12 live) plus an MCP stdio smoke test (34 live matches, Süper Lig leader Galatasaray 25 pts).

## Roadmap

- Goal scorers / match events (the detail page carries them for finished matches)
- Basketball live scores as a first-class filter (sport field is already parsed)
- Head-to-head / team form from the team pages

## License

MIT — see [LICENSE](LICENSE).

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
