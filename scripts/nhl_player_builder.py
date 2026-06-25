#!/usr/bin/env python3
"""
NHL Player Stats Builder

For each season, fetches box score data for every game and extracts
individual player stats. Builds:
  docs/data/nhl/players.json        — index of all players
  docs/data/nhl/players/{id}.json   — per-player game log

Stats captured per game:
  goals, assists, points, plus_minus, shots, hits,
  blocked_shots, penalty_minutes, faceoff_wins, faceoff_losses,
  power_play_goals, power_play_assists, short_handed_goals, short_handed_assists,
  time_on_ice, power_play_toi, short_handed_toi

Run locally:  python scripts/nhl_player_builder.py
"""

import requests
import json
import time
from pathlib import Path

BASE_URL = "https://api-web.nhle.com/v1"
SEASONS_DIR  = Path("docs/data/nhl/seasons")
PLAYERS_DIR  = Path("docs/data/nhl/players")
PLAYERS_DIR.mkdir(parents=True, exist_ok=True)

import sys
# Accept optional year range args: python nhl_player_builder.py 1967 1980
START_YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else 1967
END_YEAR   = int(sys.argv[2]) if len(sys.argv) > 2 else 2025

# Load existing player index if present
PLAYERS_INDEX_FILE = Path("docs/data/nhl/players.json")
player_index = {}  # player_id -> {id, name, teams, seasons}
if PLAYERS_INDEX_FILE.exists():
    for p in json.loads(PLAYERS_INDEX_FILE.read_text()):
        player_index[p["id"]] = p

# Load existing player game logs to avoid re-fetching
player_games = {}  # player_id -> list of game dicts
for f in PLAYERS_DIR.glob("*.json"):
    pid = f.stem
    try:
        player_games[pid] = json.loads(f.read_text())
    except:
        player_games[pid] = []

def get(url, retries=3):
    for i in range(retries):
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
    """Convert 'MM:SS' to seconds."""
    if not toi_str:
        return 0
    try:
        parts = str(toi_str).split(":")
        return int(parts[0]) * 60 + int(parts[1])
    except:
        return 0

def parse_player_stats(player, game_id, date, season, game_type, team_abbrev):
    """Extract stats from a player object in the NHL API boxscore."""
    pid  = str(player.get("playerId", ""))
    name = (player.get("name", {}) or {}).get("default", "").strip()
    pos  = player.get("position", "")

    goals      = int(player.get("goals", 0) or 0)
    assists    = int(player.get("assists", 0) or 0)
    points     = goals + assists
    plus_minus = int(player.get("plusMinus", 0) or 0)
    shots      = int(player.get("sog", 0) or 0)
    hits       = int(player.get("hits", 0) or 0)
    blocked    = int(player.get("blockedShots", 0) or 0)
    pim        = int(player.get("pim", 0) or 0)
    pp_goals   = int(player.get("powerPlayGoals", 0) or 0)
    shifts     = int(player.get("shifts", 0) or 0)
    giveaways  = int(player.get("giveaways", 0) or 0)
    takeaways  = int(player.get("takeaways", 0) or 0)
    fo_pctg    = float(player.get("faceoffWinningPctg", 0) or 0)
    toi        = toi_to_seconds(player.get("toi", ""))

    return {
        "player_id": pid,
        "name":      name,
        "position":  pos,
    }, {
        "game_id":    game_id,
        "date":       date,
        "season":     season,
        "game_type":  game_type,
        "team":       team_abbrev,
        "goals":      goals,
        "assists":    assists,
        "points":     points,
        "plus_minus": plus_minus,
        "shots":      shots,
        "hits":       hits,
        "blocked":    blocked,
        "pim":        pim,
        "pp_goals":   pp_goals,
        "shifts":     shifts,
        "giveaways":  giveaways,
        "takeaways":  takeaways,
        "fo_pctg":    fo_pctg,
        "toi":        toi,
    }

def fetch_boxscore_players(game_id, date, season, game_type):
    """Fetch boxscore and return list of (player_info, game_stats) tuples."""
    url = f"{BASE_URL}/gamecenter/{game_id}/boxscore"
    data = get(url)
    if not data:
        return []

    # Top-level team info for abbrev
    home_abbrev = data.get("homeTeam", {}).get("abbrev", "")
    away_abbrev = data.get("awayTeam", {}).get("abbrev", "")

    # Player stats are under playerByGameStats.homeTeam / awayTeam
    pgs = data.get("playerByGameStats", {})

    results = []
    for side, abbrev in [("homeTeam", home_abbrev), ("awayTeam", away_abbrev)]:
        side_data = pgs.get(side, {})
        # Grouped by position: forwards, defense, goalies
        for position_group in side_data.values():
            if not isinstance(position_group, list):
                continue
            for player in position_group:
                if not player.get("playerId"):
                    continue
                try:
                    pinfo, pstats = parse_player_stats(
                        player, game_id, date, season, game_type, abbrev
                    )
                    if pinfo["player_id"]:
                        results.append((pinfo, pstats))
                except Exception as e:
                    print(f"      WARN parse error: {e}")
    return results

# ── Main loop ────────────────────────────────────────────────────────────────

seen_game_ids = set()
# Pre-populate seen game IDs from existing player data to avoid re-fetching
for games_list in player_games.values():
    for g in games_list:
        seen_game_ids.add(g.get("game_id"))

for year in range(START_YEAR, END_YEAR + 1):
    season_file = SEASONS_DIR / f"{year}.json"
    if not season_file.exists():
        continue

    season_games = json.loads(season_file.read_text())
    if not season_games:
        print(f"SKIP {year} (no games)")
        continue

    # Filter to games not already processed
    new_games = [g for g in season_games if g.get("game_id") not in seen_game_ids]
    if not new_games:
        print(f"SKIP {year} (all {len(season_games)} games already processed)")
        continue

    print(f"\n=== SEASON {year} — {len(new_games)} new games to process ===")

    for i, game in enumerate(new_games):
        gid       = game.get("game_id")
        date      = game.get("date", "")
        gtype     = game.get("game_type", "R")

        print(f"  [{i+1}/{len(new_games)}] {gid} {date}")

        player_stats = fetch_boxscore_players(gid, date, year, gtype)

        for pinfo, pstats in player_stats:
            pid = pinfo["player_id"]

            # Update index
            if pid not in player_index:
                player_index[pid] = {
                    "id":      pid,
                    "name":    pinfo["name"],
                    "position": pinfo["position"],
                    "teams":   [],
                    "seasons": []
                }
            if pinfo["name"]:
                player_index[pid]["name"] = pinfo["name"]
            if pstats["team"] and pstats["team"] not in player_index[pid]["teams"]:
                player_index[pid]["teams"].append(pstats["team"])
            if year not in player_index[pid]["seasons"]:
                player_index[pid]["seasons"].append(year)

            # Add game to player log
            if pid not in player_games:
                player_games[pid] = []
            player_games[pid].append(pstats)

        seen_game_ids.add(gid)
        time.sleep(0.15)  # polite rate limiting

    # Save after each season
    print(f"  Saving player files for {year}...")
    for pid, games_list in player_games.items():
        f = PLAYERS_DIR / f"{pid}.json"
        f.write_text(json.dumps(games_list, separators=(",", ":")))

    # Save index
    index_list = sorted(player_index.values(), key=lambda p: p.get("name", ""))
    PLAYERS_INDEX_FILE.write_text(json.dumps(index_list, separators=(",", ":")))
    print(f"  Index: {len(player_index)} players")

print("\nDONE")
