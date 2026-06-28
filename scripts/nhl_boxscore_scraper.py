#!/usr/bin/env python3
"""
NHL Boxscore Scraper

Fetches and saves full boxscore data for every game in the season files.
Output: docs/data/nhl/boxscores/{game_id}.json

Each file contains:
  - Game info (date, teams, scores, venue, period scores)
  - Player stats for both teams (skaters and goalies)
  - Team stats (shots, hits, faceoffs, powerplays, giveaways, takeaways)

Usage:
  python scripts/nhl_boxscore_scraper.py            # all seasons
  python scripts/nhl_boxscore_scraper.py 2020 2025  # specific range
"""

import requests
import json
import time
import sys
from pathlib import Path

BASE_URL     = "https://api-web.nhle.com/v1"
SEASONS_DIR  = Path("docs/data/nhl/seasons")
BOXSCORE_DIR = Path("docs/data/nhl/boxscores")
BOXSCORE_DIR.mkdir(parents=True, exist_ok=True)

START_YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else 1967
END_YEAR   = int(sys.argv[2]) if len(sys.argv) > 2 else 2025

def get(url):
    for i in range(3):
        try:
            r = requests.get(url, timeout=30)
            if r.ok:
                return r.json()
            time.sleep(1)
        except Exception as e:
            print(f"    WARN: {e}")
            time.sleep(2)
    return {}

def toi_to_seconds(toi_str):
    if not toi_str:
        return 0
    try:
        parts = str(toi_str).split(":")
        return int(parts[0]) * 60 + int(parts[1])
    except:
        return 0

def parse_skater(p):
    return {
        "id":           p.get("playerId"),
        "name":         (p.get("name") or {}).get("default", ""),
        "number":       p.get("sweaterNumber"),
        "position":     p.get("position"),
        "goals":        p.get("goals", 0),
        "assists":      p.get("assists", 0),
        "points":       (p.get("goals", 0) or 0) + (p.get("assists", 0) or 0),
        "plus_minus":   p.get("plusMinus", 0),
        "pim":          p.get("pim", 0),
        "hits":         p.get("hits", 0),
        "shots":        p.get("sog", 0),
        "blocked":      p.get("blockedShots", 0),
        "pp_goals":     p.get("powerPlayGoals", 0),
        "shifts":       p.get("shifts", 0),
        "giveaways":    p.get("giveaways", 0),
        "takeaways":    p.get("takeaways", 0),
        "fo_pctg":      p.get("faceoffWinningPctg", 0),
        "toi":          toi_to_seconds(p.get("toi", "")),
        "toi_str":      p.get("toi", ""),
    }

def parse_goalie(p):
    return {
        "id":             p.get("playerId"),
        "name":           (p.get("name") or {}).get("default", ""),
        "number":         p.get("sweaterNumber"),
        "position":       "G",
        "saves":          p.get("saveShotsAgainst", 0),
        "shots_against":  p.get("shotsAgainst", 0),
        "goals_against":  p.get("goalsAgainst", 0),
        "save_pctg":      p.get("savePctg", 0),
        "pim":            p.get("pim", 0),
        "toi":            toi_to_seconds(p.get("toi", "")),
        "toi_str":        p.get("toi", ""),
        "starter":        p.get("starter", False),
        "decision":       p.get("decision", ""),
    }

def parse_team_stats(team_data):
    ts = team_data.get("teamGameStats", [])
    stats = {}
    for item in ts:
        cat = item.get("category", "")
        stats[cat] = {
            "home": item.get("homeValue"),
            "away": item.get("awayValue"),
        }
    return stats

def parse_boxscore(data, game_id, season):
    home = data.get("homeTeam", {})
    away = data.get("awayTeam", {})
    pgs  = data.get("playerByGameStats", {})

    # Period scores
    periods = []
    for p in data.get("periodDescriptor", {}).get("periods", []) or data.get("linescore", {}).get("periods", []):
        periods.append({
            "period":     p.get("periodDescriptor", {}).get("number") or p.get("num"),
            "home_goals": p.get("home", {}).get("goals") or p.get("homeGoals"),
            "away_goals": p.get("away", {}).get("goals") or p.get("awayGoals"),
        })

    # Shootout
    shootout = data.get("shootout", [])

    # Players
    home_skaters  = []
    home_goalies  = []
    away_skaters  = []
    away_goalies  = []

    home_pgs = pgs.get("homeTeam", {})
    away_pgs = pgs.get("awayTeam", {})

    for pos in ["forwards", "defense"]:
        for p in home_pgs.get(pos, []):
            home_skaters.append(parse_skater(p))
        for p in away_pgs.get(pos, []):
            away_skaters.append(parse_skater(p))

    for p in home_pgs.get("goalies", []):
        home_goalies.append(parse_goalie(p))
    for p in away_pgs.get("goalies", []):
        away_goalies.append(parse_goalie(p))

    # Team game stats
    team_stats = parse_team_stats(data)

    return {
        "game_id":    game_id,
        "season":     season,
        "date":       data.get("gameDate", ""),
        "game_type":  "P" if str(game_id)[4:6] == "03" else "R",
        "venue":      (data.get("venue") or {}).get("default", ""),
        "game_state": data.get("gameState", ""),
        "home": {
            "team":    home.get("abbrev", ""),
            "name":    (home.get("name") or {}).get("default", ""),
            "score":   home.get("score"),
            "sog":     home.get("sog"),
            "skaters": home_skaters,
            "goalies": home_goalies,
        },
        "away": {
            "team":    away.get("abbrev", ""),
            "name":    (away.get("name") or {}).get("default", ""),
            "score":   away.get("score"),
            "sog":     away.get("sog"),
            "skaters": away_skaters,
            "goalies": away_goalies,
        },
        "periods":  periods,
        "shootout": shootout,
        "team_stats": team_stats,
    }

# ── Main loop ────────────────────────────────────────────────────────────────

total_saved = 0
total_skipped = 0

for year in range(START_YEAR, END_YEAR + 1):
    season_file = SEASONS_DIR / f"{year}.json"
    if not season_file.exists():
        continue

    season_games = json.loads(season_file.read_text())
    if not season_games:
        print(f"SKIP {year} (no games)")
        continue

    # Filter to games not already saved
    new_games = [g for g in season_games
                 if not (BOXSCORE_DIR / f"{g['game_id']}.json").exists()]

    skipped = len(season_games) - len(new_games)
    total_skipped += skipped

    if not new_games:
        print(f"SKIP {year} (all {len(season_games)} boxscores already saved)")
        continue

    print(f"\n=== SEASON {year} — {len(new_games)} new / {skipped} already saved ===")

    for i, game in enumerate(new_games):
        gid  = game.get("game_id")
        date = game.get("date", "")

        print(f"  [{i+1}/{len(new_games)}] {gid} {date}")

        data = get(f"{BASE_URL}/gamecenter/{gid}/boxscore")
        if not data:
            print(f"    WARN: no data for {gid}")
            continue

        try:
            parsed = parse_boxscore(data, gid, year)
            out = BOXSCORE_DIR / f"{gid}.json"
            out.write_text(json.dumps(parsed, separators=(",", ":")))
            total_saved += 1
        except Exception as e:
            print(f"    WARN: parse error for {gid}: {e}")

        time.sleep(0.15)

print(f"\nDONE — {total_saved} saved, {total_skipped} skipped")
