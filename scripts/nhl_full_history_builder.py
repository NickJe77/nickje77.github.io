#!/usr/bin/env python3
"""
NHL Full History Builder (1967 → now)

Uses the NHL API season schedule endpoint — one call per season
instead of one call per day, making it ~60x faster.

Output: docs/data/nhl/seasons/{year}.json
"""

import requests
import json
import time
from pathlib import Path

print("NHL FULL HISTORY BUILDER (1967 → NOW)")

BASE = Path("docs/data/nhl/seasons")
BASE.mkdir(parents=True, exist_ok=True)

START_YEAR = 1967
END_YEAR   = 2025  # current season

# NHL team abbreviations (needed to pull per-team schedules)
# We pull one team's full season schedule which includes all games
# Using a stable franchise that's existed since 1967
PROBE_TEAM = "MTL"  # Montreal — oldest franchise, always in the league

GAME_TYPES = {2: "R", 3: "P"}  # Regular, Playoff

def fetch_season(year):
    """
    Fetch all games for a season using the club-schedule-season endpoint.
    Season ID format: 19671968, 20232024, etc.
    """
    season_id = f"{year}{year+1}"
    url = f"https://api-web.nhle.com/v1/club-schedule-season/{PROBE_TEAM}/{season_id}"
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"  WARN: club-schedule failed for {year}: {e}")
        return {}

def fetch_full_schedule(year):
    """
    Fallback: use the date-range schedule endpoint for a full season.
    Returns all games league-wide for a date range.
    """
    season_id = f"{year}{year+1}"
    url = f"https://api-web.nhle.com/v1/schedule/now"
    # Try the specific season schedule
    url2 = f"https://api-web.nhle.com/v1/standings/{year}-10-01"
    try:
        r = requests.get(f"https://api-web.nhle.com/v1/schedule/{year}-10-01", timeout=30)
        return r.json()
    except Exception as e:
        print(f"  WARN: schedule fetch failed: {e}")
        return {}

def get_all_teams_for_season(year):
    """Get all team abbreviations active in a given season."""
    season_id = f"{year}{year+1}"
    url = f"https://api-web.nhle.com/v1/standings/{year+1}-04-01"
    try:
        r = requests.get(url, timeout=30)
        data = r.json()
        teams = set()
        for entry in data.get("standings", []):
            abbrev = entry.get("teamAbbrev", {}).get("default", "")
            if abbrev:
                teams.add(abbrev)
        return list(teams)
    except Exception as e:
        print(f"  WARN: could not get teams for {year}: {e}")
        return []

def parse_game(game):
    """Parse a game object from the schedule API into our format."""
    game_type = game.get("gameType", 0)
    if game_type not in [2, 3]:
        return None

    home = game.get("homeTeam", {})
    away = game.get("awayTeam", {})

    # Score — only present for completed games
    home_score = home.get("score")
    away_score = away.get("score")

    # Game state: OFF = final, LIVE = in progress, FUT = future
    state = game.get("gameState", "")
    if state in ("FUT", "PRE"):
        return None  # Skip unplayed games

    return {
        "game_id":    game.get("id"),
        "date":       game.get("gameDate", ""),
        "game_type":  GAME_TYPES.get(game_type, "R"),
        "home_team":  home.get("abbrev", ""),
        "away_team":  away.get("abbrev", ""),
        "home_score": home_score,
        "away_score": away_score,
        "venue":      game.get("venue", {}).get("default", ""),
        "season":     game.get("season", ""),
    }

def fetch_season_via_teams(year):
    """
    Pull schedule for every team and deduplicate.
    Most reliable method — guarantees we get all games.
    """
    season_id = f"{year}{year+1}"
    teams = get_all_teams_for_season(year)

    if not teams:
        # Fallback to hardcoded list of original 6 + expansion teams
        teams = ["MTL","TOR","BOS","CHI","DET","NYR","PHI","PIT","STL",
                 "MIN","OAK","LAK","BUF","VAN","NYI","ATL","KC","WPG",
                 "COL","NJD","EDM","CGY","SJS","TBL","OTT","FLA","ANA",
                 "PHX","ARI","CAR","CBJ","NSH","DAL","WSH","VGK","SEA","UTA"]

    seen = set()
    games = []

    for team in teams:
        url = f"https://api-web.nhle.com/v1/club-schedule-season/{team}/{season_id}"
        try:
            r = requests.get(url, timeout=30)
            if not r.ok:
                continue
            data = r.json()
            for game in data.get("games", []):
                gid = game.get("id")
                if not gid or gid in seen:
                    continue
                parsed = parse_game(game)
                if parsed:
                    seen.add(gid)
                    games.append(parsed)
            time.sleep(0.1)  # be polite to the API
        except Exception as e:
            print(f"    WARN {team}: {e}")
            continue

    return sorted(games, key=lambda g: g["date"])

# ── Main loop ────────────────────────────────────────────────────────────────

for year in range(START_YEAR, END_YEAR + 1):
    out_file = BASE / f"{year}.json"

    # Skip if already built (useful for re-runs)
    if out_file.exists():
        existing = json.loads(out_file.read_text())
        if existing:
            print(f"SKIP {year} ({len(existing)} games already saved)")
            continue

    print(f"\n=== SEASON {year}-{year+1} ===")
    games = fetch_season_via_teams(year)
    print(f"  → {len(games)} games")

    out_file.write_text(json.dumps(games, indent=2))
    print(f"  Saved {out_file.name}")

    time.sleep(0.5)  # brief pause between seasons

print("\nDONE")
