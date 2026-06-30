#!/usr/bin/env python3
"""
NHL Player Stats Builder (v2 — reads from local boxscore files)

Builds player game logs and the players.json index directly from
the already-scraped boxscore files in docs/data/nhl/boxscores/,
instead of calling the NHL API again. This guarantees consistency
with the verified boxscore data and avoids API-related bugs.

Output:
  docs/data/nhl/players.json        — index of all players
  docs/data/nhl/players/{id}.json   — per-player game log

Usage:
  python scripts/nhl_player_builder.py            # all boxscores
  python scripts/nhl_player_builder.py 1979 1985  # only seasons in this range
"""

import json
import sys
from pathlib import Path

BOXSCORE_DIR = Path("docs/data/nhl/boxscores")
PLAYERS_DIR  = Path("docs/data/nhl/players")
PLAYERS_DIR.mkdir(parents=True, exist_ok=True)
INDEX_FILE   = Path("docs/data/nhl/players.json")
NAMES_FILE   = Path("docs/data/nhl/player_names.json")

START_YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else None
END_YEAR   = int(sys.argv[2]) if len(sys.argv) > 2 else None

names_cache = {}
if NAMES_FILE.exists():
    names_cache = json.loads(NAMES_FILE.read_text())
    print(f"Loaded {len(names_cache)} cached full names")

# Find all boxscore files, both flat and in season subfolders
all_files = list(BOXSCORE_DIR.glob("*.json")) + list(BOXSCORE_DIR.glob("*/*.json"))
print(f"Found {len(all_files)} boxscore files total")

if START_YEAR is not None and END_YEAR is not None:
    filtered = []
    for f in all_files:
        try:
            season = int(f.stem[:4])
        except:
            continue
        if START_YEAR <= season <= END_YEAR:
            filtered.append(f)
    all_files = filtered
    print(f"Filtered to {len(all_files)} files for seasons {START_YEAR}-{END_YEAR}")

# player_id -> list of game dicts
player_games = {}
# player_id -> {id, name, position, teams set, seasons set}
player_meta = {}

def best_name(pid, boxscore_name):
    """Prefer cached full name over whatever's in the boxscore."""
    cached = names_cache.get(str(pid)) or names_cache.get(pid)
    if cached:
        return cached
    return boxscore_name or str(pid)

def process_side(side_data, game_id, date, season, game_type, opp_team):
    team = side_data.get("team", "")
    for skater in side_data.get("skaters", []):
        pid = str(skater.get("id", ""))
        if not pid:
            continue
        name = best_name(pid, skater.get("name", ""))
        pos  = skater.get("position", "")

        record = {
            "game_id":    game_id,
            "date":       date,
            "season":     season,
            "game_type":  game_type,
            "team":       team,
            "goals":      skater.get("goals", 0),
            "assists":    skater.get("assists", 0),
            "points":     skater.get("points", (skater.get("goals",0) or 0) + (skater.get("assists",0) or 0)),
            "plus_minus": skater.get("plus_minus", 0),
            "shots":      skater.get("shots", 0),
            "hits":       skater.get("hits", 0),
            "blocked":    skater.get("blocked", 0),
            "pim":        skater.get("pim", 0),
            "pp_goals":   skater.get("pp_goals", 0),
            "shifts":     skater.get("shifts", 0),
            "giveaways":  skater.get("giveaways", 0),
            "takeaways":  skater.get("takeaways", 0),
            "fo_pctg":    skater.get("fo_pctg", 0),
            "toi":        skater.get("toi", 0),
        }

        player_games.setdefault(pid, []).append(record)

        if pid not in player_meta:
            player_meta[pid] = {"id": pid, "name": name, "position": pos, "teams": set(), "seasons": set()}
        player_meta[pid]["name"] = name  # always prefer latest/cached
        if pos:
            player_meta[pid]["position"] = pos
        if team:
            player_meta[pid]["teams"].add(team)
        if season is not None:
            player_meta[pid]["seasons"].add(season)

    for goalie in side_data.get("goalies", []):
        pid = str(goalie.get("id", ""))
        if not pid:
            continue
        name = best_name(pid, goalie.get("name", ""))

        record = {
            "game_id":       game_id,
            "date":          date,
            "season":        season,
            "game_type":     game_type,
            "team":          team,
            "saves":         goalie.get("saves", ""),
            "shots_against": goalie.get("shots_against", 0),
            "goals_against": goalie.get("goals_against", 0),
            "save_pctg":     goalie.get("save_pctg", 0),
            "pim":           goalie.get("pim", 0),
            "toi":           goalie.get("toi", 0),
            "decision":      goalie.get("decision", ""),
            "starter":       goalie.get("starter", False),
        }

        player_games.setdefault(pid, []).append(record)

        if pid not in player_meta:
            player_meta[pid] = {"id": pid, "name": name, "position": "G", "teams": set(), "seasons": set()}
        player_meta[pid]["name"] = name
        player_meta[pid]["position"] = "G"
        if team:
            player_meta[pid]["teams"].add(team)
        if season is not None:
            player_meta[pid]["seasons"].add(season)

# ── Process every boxscore file ─────────────────────────────────────────────

for i, f in enumerate(sorted(all_files)):
    try:
        data = json.loads(f.read_text())
    except Exception as e:
        print(f"  WARN: could not read {f.name}: {e}")
        continue

    game_id   = data.get("game_id")
    date      = data.get("date", "")
    season    = data.get("season")
    game_type = data.get("game_type", "R")

    home = data.get("home", {})
    away = data.get("away", {})

    process_side(home, game_id, date, season, game_type, away.get("team",""))
    process_side(away, game_id, date, season, game_type, home.get("team",""))

    if (i + 1) % 5000 == 0:
        print(f"  [{i+1}/{len(all_files)}] processed, {len(player_games)} players so far")

print(f"\nProcessed {len(all_files)} boxscores -> {len(player_games)} players")

# ── Save per-player files ───────────────────────────────────────────────────

for pid, games in player_games.items():
    out = PLAYERS_DIR / f"{pid}.json"
    # Merge with existing file if present and we're doing a partial year-range run
    if START_YEAR is not None and out.exists():
        try:
            existing = json.loads(out.read_text())
            existing_ids = set((g["game_id"], g.get("team")) for g in existing)
            new_only = [g for g in games if (g["game_id"], g.get("team")) not in existing_ids]
            games = existing + new_only
        except Exception:
            pass
    games.sort(key=lambda g: (g.get("season") or 0, g.get("date") or ""))
    out.write_text(json.dumps(games, separators=(",", ":")))

print(f"Saved {len(player_games)} player files")

# ── Build / merge players.json index ────────────────────────────────────────

existing_index = {}
if INDEX_FILE.exists():
    for p in json.loads(INDEX_FILE.read_text()):
        existing_index[p["id"]] = p

for pid, meta in player_meta.items():
    entry = existing_index.get(pid, {"id": pid, "name": meta["name"], "position": meta["position"], "teams": [], "seasons": []})
    entry["name"] = meta["name"]
    if meta["position"]:
        entry["position"] = meta["position"]
    existing_teams = set(entry.get("teams", []))
    existing_teams.update(meta["teams"])
    entry["teams"] = sorted(existing_teams)
    existing_seasons = set(entry.get("seasons", []))
    existing_seasons.update(meta["seasons"])
    entry["seasons"] = sorted(existing_seasons)
    existing_index[pid] = entry

index_list = sorted(existing_index.values(), key=lambda p: p.get("name", ""))
INDEX_FILE.write_text(json.dumps(index_list, separators=(",", ":")))
print(f"Saved players.json with {len(index_list)} players")

print("\nDONE")
