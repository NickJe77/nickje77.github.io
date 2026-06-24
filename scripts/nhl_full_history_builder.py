#!/usr/bin/env python3
"""
NHL Full History Builder (1967 → now)

Regular season: club-schedule-season endpoint (one call per team)
Playoffs: probe game IDs directly using NHL ID format:
  {season_start}030{round}{series}{game}
  e.g. 2019030111 = 2019 season, round 1, series 1, game 1
  Rounds 1-4, series 1-8, games 1-7

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
    data = get(f"https://api-web.nhle.com/v1/standings/{year+1}-04-01")
    teams = set()
    for entry in data.get("standings", []):
        abbrev = entry.get("teamAbbrev", {}).get("default", "")
        if abbrev:
            teams.add(abbrev)
    return list(teams)

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

def fetch_playoffs_by_id(year, seen):
    """
    Probe playoff game IDs directly using the NHL ID format:
      {year}03{round}{series}{game}
    e.g. 2024030111 = 2024 season, playoff, round 1, series 1, game 1
    Rounds 1-4, up to 8 series per round, up to 7 games per series.
    Only ~224 possible IDs per season — very fast.
    """
    games = []

    for round_num in range(1, 5):        # rounds 1-4
        for series_num in range(1, 9):   # up to 8 series per round
            for game_num in range(1, 8): # up to 7 games per series
                # NHL playoff ID format: YYYY03RRSSGG
                # e.g. 2024030111 = 2024-25 season, round 1, series 1, game 1
                game_id = int(f"{year}030{round_num}{series_num}{game_num}")

                if game_id in seen:
                    continue

                data = get(f"https://api-web.nhle.com/v1/gamecenter/{game_id}/boxscore")
                if not data or not data.get("homeTeam"):
                    # No game at this ID — series is done, skip remaining games
                    break

                home = data.get("homeTeam", {})
                away = data.get("awayTeam", {})
                state = data.get("gameState", "")

                if state in ("FUT", "PRE"):
                    continue

                parsed = {
                    "game_id":    game_id,
                    "date":       data.get("gameDate", ""),
                    "game_type":  "P",
                    "home_team":  home.get("abbrev", ""),
                    "away_team":  away.get("abbrev", ""),
                    "home_score": home.get("score"),
                    "away_score": away.get("score"),
                    "venue":      data.get("venue", {}).get("default", ""),
                }
                seen.add(game_id)
                games.append(parsed)
                time.sleep(0.1)

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

        # Backfill game_type from game_id for all existing games missing it
        changed = False
        for g in existing:
            if not g.get("game_type"):
                gid = str(g.get("game_id", ""))
                g["game_type"] = "P" if len(gid) >= 6 and gid[4:6] == "03" else "R"
                changed = True

        if changed:
            out_file.write_text(json.dumps(existing, indent=2))
            print(f"  Backfilled game_type for {year}")

        # Re-check playoffs after backfill
        has_playoffs = any(g.get("game_type") == "P" for g in existing)
        if has_playoffs:
            print(f"SKIP {year} (playoffs now present after backfill)")
            continue

        # Has regular season but missing playoffs — patch
        print(f"\n=== PATCHING PLAYOFFS {year}-{year+1} ===")
        seen = set(g["game_id"] for g in existing)
        po = fetch_playoffs_by_id(year, seen)
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
    po  = fetch_playoffs_by_id(year, seen)
    print(f"  Playoffs: {len(po)}")
    all_games = sorted(reg + po, key=lambda g: g.get("date") or "")
    out_file.write_text(json.dumps(all_games, indent=2))
    print(f"  Saved {out_file.name} ({len(all_games)} total)")
    time.sleep(0.5)

print("\nDONE")
