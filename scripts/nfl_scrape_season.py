#!/usr/bin/env python3
"""
nfl_scrape_season.py  (nflverse-data version)

Both pro-football-reference.com (Cloudflare "Just a moment" challenge) and
site.api.espn.com (plain 403) block requests coming from GitHub Actions'
shared runner IPs. Rather than scrape either site directly, this version
downloads the pre-built, continuously-updated schedule/results file that
the nflverse project already publishes as a GitHub Release asset:

    https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv

That's a plain GitHub download (not a scrape target), so it always works
from GitHub Actions. games.csv covers every season 1999-present and is
updated same-day as games are played.

Output schema for docs/data/nfl/seasons/{season}.json is UNCHANGED:
    { "season": int, "source": url, "updated": iso timestamp,
      "games": [ { "game_id", "date", "week", "team1", "team2",
                   "score1", "score2", "venue" }, ... ] }

NOTE: this version does NOT populate per-game boxscores
(docs/data/nfl/boxscores/{season}/*.json). nflverse's player-level stats
release (player_stats.csv) has not been updated since May 2025, so it does
not have current-season data, and no other bot-wall-free source was found.
Boxscores/player leaders for new games are a separate, still-open problem
until we find a live source. Existing boxscore files already in the repo
are left untouched (never deleted).

Usage:
    python3 scripts/nfl_scrape_season.py 2026
"""

import csv
import io
import json
import os
import sys
import datetime as dt

import requests

GAMES_CSV_URL = "https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv"

OUT_ROOT = "docs/data/nfl"
SEASONS_DIR = f"{OUT_ROOT}/seasons"

TEAM_NAMES = {
    "ARI": "Arizona Cardinals", "ATL": "Atlanta Falcons", "BAL": "Baltimore Ravens",
    "BUF": "Buffalo Bills", "CAR": "Carolina Panthers", "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals", "CLE": "Cleveland Browns", "DAL": "Dallas Cowboys",
    "DEN": "Denver Broncos", "DET": "Detroit Lions", "GB": "Green Bay Packers",
    "HOU": "Houston Texans", "IND": "Indianapolis Colts", "JAX": "Jacksonville Jaguars",
    "KC": "Kansas City Chiefs", "LA": "Los Angeles Rams", "LAC": "Los Angeles Chargers",
    "LV": "Las Vegas Raiders", "MIA": "Miami Dolphins", "MIN": "Minnesota Vikings",
    "NE": "New England Patriots", "NO": "New Orleans Saints", "NYG": "New York Giants",
    "NYJ": "New York Jets", "PHI": "Philadelphia Eagles", "PIT": "Pittsburgh Steelers",
    "SEA": "Seattle Seahawks", "SF": "San Francisco 49ers", "TB": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans", "WAS": "Washington Commanders",
    # legacy/alternate codes seen in older seasons of this file
    "OAK": "Oakland Raiders", "SD": "San Diego Chargers", "STL": "St. Louis Rams",
}


def team_name(code):
    return TEAM_NAMES.get(code, code)


def to_int(val):
    try:
        return int(float(val))
    except (TypeError, ValueError):
        return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/nfl_scrape_season.py <season>")
        sys.exit(1)

    season = int(sys.argv[1])

    print(f"Downloading {GAMES_CSV_URL} ...")
    res = requests.get(GAMES_CSV_URL, timeout=60)
    res.raise_for_status()
    print(f"  got {len(res.content)} bytes")

    reader = csv.DictReader(io.StringIO(res.text))

    games = []
    for row in reader:
        if row.get("season") != str(season):
            continue

        games.append({
            "game_id": row.get("game_id", ""),
            "date": row.get("gameday", ""),
            "week": row.get("week", ""),
            "team1": team_name(row.get("away_team", "")),
            "team2": team_name(row.get("home_team", "")),
            "score1": to_int(row.get("away_score")),
            "score2": to_int(row.get("home_score")),
            "venue": row.get("stadium", "") or "",
        })

    os.makedirs(SEASONS_DIR, exist_ok=True)
    season_out = {
        "season": season,
        "source": GAMES_CSV_URL,
        "updated": dt.datetime.now(dt.timezone.utc).isoformat(),
        "games": games,
    }
    with open(f"{SEASONS_DIR}/{season}.json", "w", encoding="utf-8") as f:
        json.dump(season_out, f, indent=2, ensure_ascii=False)

    played = sum(1 for g in games if g["score1"] is not None)
    print(f"Wrote {SEASONS_DIR}/{season}.json ({len(games)} games, {played} with a final score)")
    print("NOTE: boxscores were NOT updated by this script — see file header.")


if __name__ == "__main__":
    main()
