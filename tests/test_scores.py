"""Offline tests for mackolik_mcp.scores — recorded real feed data.

Fixtures are real responses fetched 2026-11-07 (curl, browser UA):
- livedata-today.json: vd.mackolik.com/livedata?group=0 (836 matches
  for 07/11/2026: Süper Lig Eyüpspor-Kocaelispor 13:30 upcoming,
  live Melbourne City-Western Sydney 81' 1-1, finished Jeju-Gwangju
  1-1 MS, Galatasaray-Amed SK 19:00).
- standings-tur.html: StandingHandler.aspx?league=Tur (Süper Lig:
  1. Galatasaray 10 played, 25 pts, +11).
"""
import json
import os
import unittest

from mackolik_mcp import scores as S

FIX = os.path.join(os.path.dirname(__file__), "fixtures")


def _read(name: str) -> str:
    with open(os.path.join(FIX, name), encoding="utf-8") as f:
        return f.read()


class TestNormalizeDate(unittest.TestCase):
    def test_iso(self):
        self.assertEqual(S.normalize_date("2026-11-07"), "07/11/2026")

    def test_tr(self):
        self.assertEqual(S.normalize_date("07/11/2026"), "07/11/2026")
        self.assertEqual(S.normalize_date("07.11.2026"), "07/11/2026")

    def test_bad(self):
        with self.assertRaises(ValueError):
            S.normalize_date("tomorrow")

    def test_today(self):
        import re

        self.assertRegex(S.today_tr(), r"^\d{2}/\d{2}/\d{4}$")


class TestParseLivedata(unittest.TestCase):
    def setUp(self):
        self.matches = S.parse_livedata(_read("livedata-today.json"))

    def test_count(self):
        self.assertEqual(len(self.matches), 836)

    def test_super_lig_upcoming(self):
        row = next(m for m in self.matches if m["match_id"] == 4542744)
        self.assertEqual(row["home_team"], "Eyüpspor")
        self.assertEqual(row["away_team"], "Kocaelispor")
        self.assertEqual(row["league"], "Süper Lig")
        self.assertEqual(row["country"], "Türkiye")
        self.assertEqual(row["date"], "07/11/2026")
        self.assertEqual(row["time"], "13:30")
        self.assertEqual(row["status"], "upcoming")
        self.assertIsNone(row["home_goals"])
        self.assertEqual(row["odds_1"], "3.83")
        self.assertEqual(row["odds_x"], "3.02")
        self.assertEqual(row["odds_2"], "1.68")
        self.assertEqual(
            row["url"],
            "https://arsiv.mackolik.com/Futbol-Mac/4542744/eyupspor-kocaelispor",
        )

    def test_galatasaray_fixture(self):
        row = next(m for m in self.matches if m["match_id"] == 4542749)
        self.assertEqual(row["home_team"], "Galatasaray")
        self.assertEqual(row["away_team"], "Amed SK")
        self.assertEqual(row["time"], "19:00")

    def test_live_match(self):
        row = next(m for m in self.matches if m["match_id"] == 4546754)
        self.assertEqual(row["status"], "live")
        self.assertEqual(row["status_text"], "81")
        self.assertEqual((row["home_goals"], row["away_goals"]), (1, 1))
        self.assertEqual(row["red_cards_home"], 1)

    def test_finished_match(self):
        row = next(m for m in self.matches if m["match_id"] == 4578080)
        self.assertEqual(row["status"], "finished")
        self.assertEqual(row["status_text"], "MS")
        self.assertEqual((row["home_goals"], row["away_goals"]), (1, 1))
        self.assertEqual(row["league"], "K Lig 1 Küme Düşme Turu")

    def test_status_buckets(self):
        by_status = {}
        for m in self.matches:
            by_status[m["status"]] = by_status.get(m["status"], 0) + 1
        self.assertGreater(by_status.get("live", 0), 0)
        self.assertGreater(by_status.get("finished", 0), 0)
        self.assertGreater(by_status.get("upcoming", 0), 0)

    def test_league_filter(self):
        # "Süper Lig" is also the league name in Greece, Switzerland,
        # Serbia, Slovakia, India, Indonesia — plus substring hits
        # like "Kadınlar Süper Lig" and "Basketbol Süper Ligi".
        all_super = S.filter_matches(self.matches, league="Süper Lig")
        self.assertGreaterEqual(len(all_super), 20)
        tur = [m for m in all_super
               if m["country"] == "Türkiye" and m["league"] == "Süper Lig"]
        self.assertEqual(len(tur), 4)
        eng = S.filter_matches(self.matches, league="Premier Lig")
        self.assertGreater(len(eng), 0)

    def test_live_scoreless_is_nil_nil(self):
        # a live match with a blank score field is 0-0 (no goal yet)
        row = [999999, 1, "Ev", 2, "Dep", 1, "17", "", 0, 0, 0, 0, 0,
               0, 0, {"h1": 0, "h2": 0, "k1": 0, "k2": 0}, "13:30", 0,
               "2.00", "3.00", "2.80", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, "07/11/2026",
               [1, "Türkiye", 1, "Süper Lig", 1, "2026/2027"], "1"]
        m = S.parse_match(row)
        self.assertEqual(m["status"], "live")
        self.assertEqual(m["score"], "0-0")
        self.assertEqual((m["home_goals"], m["away_goals"]), (0, 0))

    def test_bad_json(self):
        with self.assertRaises(ValueError):
            S.parse_livedata("not json")


class TestParseStandings(unittest.TestCase):
    def test_tur(self):
        rows = S.parse_standings(_read("standings-tur.html"))
        self.assertGreaterEqual(len(rows), 9)
        first = rows[0]
        self.assertEqual(first["rank"], 1)
        self.assertEqual(first["team"], "Galatasaray")
        self.assertEqual(first["played"], 10)
        self.assertEqual(first["points"], 25)
        self.assertEqual(first["goal_difference"], 11)
        self.assertEqual(rows[1]["team"], "Amed SK")
        self.assertEqual(rows[1]["points"], 23)


if __name__ == "__main__":
    unittest.main()
