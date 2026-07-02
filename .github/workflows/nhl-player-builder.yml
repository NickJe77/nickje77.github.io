#!/usr/bin/env python3
"""
NHL Player Stats Builder (v3 — fetches boxscores live, no local storage)

Fetches boxscores from the NHL API on the fly during the run.
Does NOT save boxscore files to disk — processes and discards them.
Only saves per-player game logs and the players.json index.

Output:
  docs/data/nhl/players.json        — index of all players
  docs/data/nhl/players/{id}.json   — per-player game log

Usage:
  python scripts/nhl_player_builder.py            # all seasons
  python scripts/nhl_player_builder.py 2024 2025  # specific range
"""

import requests
import json
import time
import sys
from pathlib import Path

BASE_URL     = "https://api-web.nhle.com/v1"
SEASONS_DIR  = Path("docs/data/nhl/seasons")
PLAYERS_DIR  = Path("docs/data/nhl/players")
PLAYERS_DIR.mkdir(parents=True, exist_ok=True)
INDEX_FILE   = Path("docs/data/nhl/players.json")
NAMES_FILE   = Path("docs/data/nhl/player_names.json")

START_YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else None
END_YEAR   = int(sys.argv[2]) if len(sys.argv) > 2 else None

# Load name cache
names_cache = {}
if NAMES_FILE.exists():
    names_cache = json.loads(NAMES_FILE.read_text())
    print(f"Loaded {len(names_cache)} cached full names")

# Load existing player index and build seen game IDs
existing_index = {}
if INDEX_FILE.exists():
    for p in json.loads(INDEX_FILE.read_text()):
        existing_index[p["id"]] = p

# Build set of already-processed game IDs from existing player files
seen_game_ids = set()
for f in PLAYERS_DIR.glob("*.json"):
    try:
        games = json.loads(f.read_text())
        for g in games:
            seen_game_ids.add(str(g.get("game_id","")))
    except:
        pass
print(f"Already processed: {len(seen_game_ids)} game entries across existing player files")

def get(url, retries=3):
    for i in range(retries):
        try:
            r = requests.get(url, timeout=30)
            if r.ok:
                return r.json()
            time.sleep(1)
        except Exception as e:
            print(f"  WARN: {e}")
            time.sleep(2)
    return {}

def best_name(pid, fallback=""):
    return names_cache.get(str(pid)) or fallback or str(pid)

def toi_to_seconds(toi_str):
    if not toi_str:
        return 0
    try:
        parts = str(toi_str).split(":")
        return int(parts[0]) * 60 + int(parts[1])
    except:
        return 0

def process_boxscore(data, game_id, season, game_type):
    """Extract player stats from a live-fetched boxscore."""
    home_abbrev = data.get("homeTeam", {}).get("abbrev", "")
    away_abbrev = data.get("awayTeam", {}).get("abbrev", "")
    pgs = data.get("playerByGameStats", {})
    date = data.get("gameDate", "")

    results = {}  # pid -> (meta, stat)

    for side, abbrev in [("homeTeam", home_abbrev), ("awayTeam", away_abbrev)]:
        side_data = pgs.get(side, {})

        for pos_group in ["forwards", "defense"]:
            for p in side_data.get(pos_group, []):
                pid = str(p.get("playerId", ""))
                if not pid:
                    continue
                name = best_name(pid, (p.get("name") or {}).get("default", ""))
                results[pid] = {
                    "meta": {"id": pid, "name": name, "position": p.get("position",""), "team": abbrev},
                    "stat": {
                        "game_id":    game_id,
                        "date":       date,
                        "season":     season,
                        "game_type":  game_type,
                        "team":       abbrev,
                        "goals":      p.get("goals", 0) or 0,
                        "assists":    p.get("assists", 0) or 0,
                        "points":     (p.get("goals",0) or 0) + (p.get("assists",0) or 0),
                        "plus_minus": p.get("plusMinus", 0) or 0,
                        "shots":      p.get("sog", 0) or 0,
                        "hits":       p.get("hits", 0) or 0,
                        "blocked":    p.get("blockedShots", 0) or 0,
                        "pim":        p.get("pim", 0) or 0,
                        "pp_goals":   p.get("powerPlayGoals", 0) or 0,
                        "shifts":     p.get("shifts", 0) or 0,
                        "giveaways":  p.get("giveaways", 0) or 0,
                        "takeaways":  p.get("takeaways", 0) or 0,
                        "fo_pctg":    p.get("faceoffWinningPctg", 0) or 0,
                        "toi":        toi_to_seconds(p.get("toi", "")),
                    }
                }

        for p in side_data.get("goalies", []):
            pid = str(p.get("playerId", ""))
            if not pid:
                continue
            name = best_name(pid, (p.get("name") or {}).get("default", ""))
            results[pid] = {
                "meta": {"id": pid, "name": name, "position": "G", "team": abbrev},
                "stat": {
                    "game_id":       game_id,
                    "date":          date,
                    "season":        season,
                    "game_type":     game_type,
                    "team":          abbrev,
                    "saves":         p.get("saveShotsAgainst", ""),
                    "shots_against": p.get("shotsAgainst", 0) or 0,
                    "goals_against": p.get("goalsAgainst", 0) or 0,
                    "save_pctg":     p.get("savePctg", 0) or 0,
                    "pim":           p.get("pim", 0) or 0,
                    "toi":           toi_to_seconds(p.get("toi", "")),
                    "decision":      p.get("decision", ""),
                    "starter":       p.get("starter", False),
                }
            }

    return results

# ── Main loop ────────────────────────────────────────────────────────────────

player_games = {}   # pid -> list of game stats
player_meta  = {}   # pid -> {id, name, position, teams, seasons}

for year in range(START_YEAR or 1967, (END_YEAR or 2025) + 1):
    season_file = SEASONS_DIR / f"{year}.json"
    if not season_file.exists():
        continue

    season_games = json.loads(season_file.read_text())
    if not season_games:
        print(f"SKIP {year} (no games)")
        continue

    new_games = [g for g in season_games if str(g.get("game_id","")) not in seen_game_ids]
    if not new_games:
        print(f"SKIP {year} (all {len(season_games)} already processed)")
        continue

    print(f"\n=== SEASON {year} — {len(new_games)} new games ===")

    for i, game in enumerate(new_games):
        gid       = str(game.get("game_id",""))
        gtype     = game.get("game_type", "R") or ("P" if gid[4:6]=="03" else "R")

        data = get(f"{BASE_URL}/gamecenter/{gid}/boxscore")
        if not data:
            print(f"  [{i+1}] {gid} — no data")
            continue

        entries = process_boxscore(data, gid, year, gtype)

        for pid, entry in entries.items():
            meta = entry["meta"]
            stat = entry["stat"]
            player_games.setdefault(pid, []).append(stat)

            if pid not in player_meta:
                player_meta[pid] = {"id": pid, "name": meta["name"],
                                    "position": meta["position"],
                                    "teams": set(), "seasons": set()}
            player_meta[pid]["name"] = meta["name"]
            if meta["position"]: player_meta[pid]["position"] = meta["position"]
            player_meta[pid]["teams"].add(meta["team"])
            player_meta[pid]["seasons"].add(year)

        seen_game_ids.add(gid)
        time.sleep(0.15)

        if (i+1) % 100 == 0:
            print(f"  [{i+1}/{len(new_games)}] processed")

    # Save after each season
    for pid, games in player_games.items():
        out = PLAYERS_DIR / f"{pid}.json"
        existing = []
        if out.exists():
            try: existing = json.loads(out.read_text())
            except: pass
        existing_ids = set(str(g["game_id"]) for g in existing)
        new_only = [g for g in games if str(g["game_id"]) not in existing_ids]
        all_games = sorted(existing + new_only, key=lambda g: (g.get("season") or 0, g.get("date") or ""))
        out.write_text(json.dumps(all_games, separators=(",",":")))

    player_games = {}  # clear memory

    # Update index
    for pid, meta in player_meta.items():
        entry = existing_index.get(pid, {"id":pid,"name":meta["name"],"position":meta["position"],"teams":[],"seasons":[]})
        entry["name"] = meta["name"]
        if meta["position"]: entry["position"] = meta["position"]
        existing_teams = set(entry.get("teams",[]))
        existing_teams.update(meta["teams"])
        entry["teams"] = sorted(existing_teams)
        existing_seasons = set(entry.get("seasons",[]))
        existing_seasons.update(meta["seasons"])
        entry["seasons"] = sorted(existing_seasons)
        existing_index[pid] = entry

    index_list = sorted(existing_index.values(), key=lambda p: p.get("name",""))
    INDEX_FILE.write_text(json.dumps(index_list, separators=(",",":")))
    print(f"  Saved index: {len(index_list)} players")

print("\nDONE")
