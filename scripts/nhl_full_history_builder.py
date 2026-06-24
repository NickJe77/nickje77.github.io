#!/usr/bin/env python3
"""
NHL Full History Builder (1967 → now)

Fetches regular season games via club-schedule-season (fast, one call per team)
AND playoff games via date-by-date schedule scan (April-June of the following year).

Output: docs/data/nhl/seasons/{year}.json
"""

import requests
import json
import time
from pathlib import Path
from datetime import datetime, timedelta

print("NHL FULL HISTORY BUILDER (1967 → NOW)")

BASE = Path("docs/data/nhl/seasons")
BASE.mkdir(parents=True, exist_ok=True)

START_YEAR = 1967
END_YEAR   = 2025

GAME_TYPES = {2: "R", 3: "P"}

def get(url):
    for i in range(3):
        try:
            r = requests.get(url, timeout=30)
            if r.ok:
                return r.json()
            time.sleep(1)
        except Exception as e:
            print(f"  WARN: {e}")
            time.sleep(2)
    return {}

def get_all_teams_for_season(year):
    url = f"https://api-web.nhle.com/v1/standings/{year+1}-04-01"
    try:
        data = get(url)
        teams = set()
        for entry in data.get("standings", []):
            abbrev = entry.get("teamAbbrev", {}).get("default", "")
            if abbrev:
                teams.add(abbrev)
        return list(teams)
    except:
        return []

FALLBACK_TEAMS = [
    "MTL","TOR","BOS","CHI","DET","NYR","PHI","PIT","STL",
    "MIN","OAK","LAK","BUF","VAN","NYI","ATL","WPG",
    "COL","NJD","EDM","CGY","SJS","TBL","OTT","FLA","ANA",
    "PHX","ARI","CAR","CBJ","NSH","DAL","WSH","VGK","SEA","UTA"
]

def parse_game(game):
    game_type = game.get("gameType", 0)
    if game_type not in [2, 3]:
        return None
    state = game.get("gameState", "")
    if state in ("FUT", "PRE"):
        return None
    home = game.get("homeTeam", {})
    away = game.get("awayTeam", {})
    return {
        "game_id":    game.get("id"),
        "date":       game.get("gameDate", ""),
        "game_type":  GAME_TYPES.get(game_type, "R"),
        "home_team":  home.get("abbrev", ""),
        "away_team":  away.get("abbrev", ""),
        "home_score": home.get("score"),
        "away_score": away.get("score"),
        "venue":      game.get("venue", {}).get("default", ""),
    }

def fetch_regular_season(year, seen):
    season_id = f"{year}{year+1}"
    teams = get_all_teams_for_season(year) or FALLBACK_TEAMS
    games = []
    for team in teams:
        data = get(f"https://api-web.nhle.com/v1/club-schedule-season/{team}/{season_id}")
        for game in data.get("games", []):
            gid = game.get("id")
            if not gid or gid in seen:
                continue
            parsed = parse_game(game)
            if parsed and parsed["game_type"] == "R":
                seen.add(gid)
                games.append(parsed)
        time.sleep(0.1)
    return games

def fetch_playoffs(year, seen):
    """Scan Apr 1 – Sep 30 of the following calendar year for playoff games.
    Extended to September to cover bubble seasons (e.g. 2019-20 played Aug-Sep 2020).
    """
    games = []
    current = datetime(year + 1, 4, 1)
    end     = datetime(year + 1, 9, 30)
    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        data = get(f"https://api-web.nhle.com/v1/schedule/{date_str}")
        for week in data.get("gameWeek", []):
            for game in week.get("games", []):
                gid = game.get("id")
                if game.get("gameType") != 3:
                    continue
                if not gid or gid in seen:
                    continue
                parsed = parse_game(game)
                if parsed:
                    seen.add(gid)
                    games.append(parsed)
        time.sleep(0.2)
        current += timedelta(days=1)
    return games

# ── Main loop ────────────────────────────────────────────────────────────────

for year in range(START_YEAR, END_YEAR + 1):
    out_file = BASE / f"{year}.json"

    if out_file.exists():
        existing = json.loads(out_file.read_text())
        has_playoffs = any(g.get("game_type") == "P" for g in existing)

        if not existing or year == 2004:
            print(f"SKIP {year} (lockout/empty)")
            continue

        if has_playoffs:
            print(f"SKIP {year} ({len(existing)} games incl. playoffs)")
            continue

        # Has regular season but missing playoffs — patch
        print(f"\n=== PATCHING PLAYOFFS {year}-{year+1} ===")
        seen = set(g["game_id"] for g in existing)
        po = fetch_playoffs(year, seen)
        print(f"  → {len(po)} playoff games found")
        if po:
            all_games = sorted(existing + po, key=lambda g: g.get("date") or "")
            out_file.write_text(json.dumps(all_games, indent=2))
            print(f"  Saved ({len(all_games)} total)")
        continue

    print(f"\n=== SEASON {year}-{year+1} ===")
    seen = set()
    reg = fetch_regular_season(year, seen)
    print(f"  Regular: {len(reg)}")
    po  = fetch_playoffs(year, seen)
    print(f"  Playoffs: {len(po)}")
    all_games = sorted(reg + po, key=lambda g: g.get("date") or "")
    out_file.write_text(json.dumps(all_games, indent=2))
    print(f"  Saved {out_file.name} ({len(all_games)} total)")
    time.sleep(0.5)

print("\nDONE")
