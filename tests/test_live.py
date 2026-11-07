"""Live tests for mackolik_mcp — real requests to mackolik.com.

Requires network + Chrome TLS impersonation (curl-cffi). The server
is polite by design (~0.8s between requests), so this file takes
~10s. Run: python -m unittest discover -s tests -v

Scores change during the day; tests assert structure and sane
ranges, not exact scores.
"""
import json
import unittest

from mackolik_mcp import http as H
from mackolik_mcp import scores as S


class TestLiveFeed(unittest.TestCase):
    def test_group_feed(self):
        matches = S.parse_livedata(H.fetch_livedata_group(0))
        self.assertGreater(len(matches), 100)
        statuses = {m["status"] for m in matches}
        self.assertIn("upcoming", statuses)
        m0 = matches[0]
        for key in ("match_id", "home_team", "away_team", "league",
                    "date", "time", "status", "url"):
            self.assertIn(key, m0)

    def test_date_feed(self):
        matches = S.parse_livedata(
            H.fetch_livedata_date(S.today_tr())
        )
        self.assertGreater(len(matches), 100)
        # the feed is (almost) all the requested date, with at most a
        # straggler from the next day — the tools filter to the date
        today = [m for m in matches if m["date"] == S.today_tr()]
        self.assertGreater(len(today), 100)
        self.assertTrue(all(m["date"] == S.today_tr() for m in today))

    def test_super_lig_today(self):
        matches = S.parse_livedata(H.fetch_livedata_group(0))
        tur = S.filter_matches(matches, league="Süper Lig")
        self.assertGreater(len(tur), 0)
        tr_super = [m for m in tur if m["country"] == "Türkiye"
                    and m["league"] == "Süper Lig"]
        self.assertGreater(len(tr_super), 0)


class TestLiveStandings(unittest.TestCase):
    def test_tur(self):
        rows = S.parse_standings(H.fetch_standings("Tur"))
        self.assertGreaterEqual(len(rows), 9)
        self.assertEqual(rows[0]["rank"], 1)
        self.assertTrue(rows[0]["team"])
        self.assertGreater(rows[0]["points"], 0)

    def test_eng(self):
        rows = S.parse_standings(H.fetch_standings("Eng"))
        self.assertGreaterEqual(len(rows), 9)


class TestLiveServerTools(unittest.TestCase):
    """End-to-end: call the MCP tool functions and check JSON output."""

    def test_live_scores_tool(self):
        from mackolik_mcp.server import mackolik_live_scores

        out = json.loads(mackolik_live_scores(limit=5))
        self.assertIn("total_live", out)
        self.assertIn("matches", out)
        self.assertLessEqual(len(out["matches"]), 5)
        for m in out["matches"]:
            self.assertEqual(m["status"], "live")

    def test_results_tool(self):
        from mackolik_mcp.server import mackolik_results

        out = json.loads(mackolik_results(limit=5))
        self.assertEqual(out["date"], S.today_tr())
        self.assertIn("matches", out)
        for m in out["matches"]:
            self.assertEqual(m["status"], "finished")

    def test_fixtures_tool(self):
        from mackolik_mcp.server import mackolik_fixtures

        out = json.loads(mackolik_fixtures(league="Süper Lig", limit=5))
        self.assertGreater(out["total_upcoming"], 0)
        self.assertTrue(
            all(m["league"] == "Süper Lig" for m in out["matches"])
        )

    def test_standings_tool(self):
        from mackolik_mcp.server import mackolik_standings

        out = json.loads(mackolik_standings("Tur"))
        self.assertEqual(out["league_name"], "Türkiye")
        self.assertGreaterEqual(out["count"], 9)

    def test_match_detail_tool(self):
        from mackolik_mcp.server import (
            mackolik_fixtures, mackolik_match_detail,
        )

        fx = json.loads(mackolik_fixtures(limit=1))
        mid = fx["matches"][0]["match_id"]
        out = json.loads(mackolik_match_detail(mid))
        self.assertEqual(out["match_id"], mid)
        self.assertTrue(out["home_team"])
        self.assertTrue(out["url"].startswith(
            "https://arsiv.mackolik.com/Futbol-Mac/"))

    def test_bad_league_error(self):
        from mackolik_mcp.server import mackolik_standings

        out = json.loads(mackolik_standings("Xyz"))
        self.assertIn("error", out)

    def test_unknown_match_error(self):
        from mackolik_mcp.server import mackolik_match_detail

        out = json.loads(mackolik_match_detail(1))
        self.assertIn("error", out)


if __name__ == "__main__":
    unittest.main()
