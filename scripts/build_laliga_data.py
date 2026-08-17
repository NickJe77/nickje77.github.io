#!/usr/bin/env python3

"""
build_laliga_data.py

Reads all match JSON files from docs/data/laliga/matches/<season>/*.json
and generates three output files:

- docs/data/la_liga/players.json
- docs/data/la_liga/teams.json
- docs/data/la_liga/team-stats.json

Note the folder split: match data lives under docs/data/laliga/ (no
underscore), but the pages that consume the summary files
(laliga.html, laliga-h2h.html, laliga-players.html, laliga-records.html)
fetch them from docs/data/la_liga/ (with underscore). This script reads
from one and writes to the other on purpose - that's not a typo.

Place this file in the scripts/ folder.
Run from the root of your GitHub repo (nickje77.github.io/)
"""

import json
import sys
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).parent.parent
MATCHES_DIR = REPO_ROOT / "docs" / "data" / "laliga" / "matches"
OUT_DIR = REPO_ROOT / "docs" / "data" / "la_liga"

# ── Helpers ───────────────────────────────────────────────────────────────
def collect_json_files(directory: Path) -> list:
    if not directory.exists():
        print(f"❌ Matches directory not found: {directory}", file=sys.stderr)
        sys.exit(1)
    return sorted(directory.rglob("*.json"))

def season_from_path(file_path: Path) -> str:
    parts = file_path.parts
    try:
        idx = list(parts).index("matches")
        return parts[idx + 1]
    except (ValueError, IndexError):
        return "unknown"

def write_json(file_path: Path, data):
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Written: {file_path}")

def make_team_stats(team: str, season: str) -> dict:
    return {
        "team": team,
        "season": season,
        "played": 0,
        "wins": 0,
        "draws": 0,
        "losses": 0,
        "goals_for": 0,
        "goals_against": 0,
        "goal_difference": 0,
        "points": 0,
        "clean_sheets": 0,
        "yellow_cards": 0,
        "red_cards": 0,
    }

def make_player(name: str) -> dict:
    return {
        "name": name,
        "teams": [],
        "seasons": [],
        "goals": 0,
        "penalties": 0,
        "own_goals": 0,
        "yellow_cards": 0,
        "red_cards": 0,
        "season_stats": []
    }

def get_or_create_team_stats(team_stats_map, team, season):
    key = f"{team}|{season}"
    if key not in team_stats_map:
        team_stats_map[key] = make_team_stats(team, season)
    return team_stats_map[key]

def find_player_key(players_map, name, team):
    """
    Find the right player entry using name + team.
    - If we've seen this exact name+team combo before, return that key.
    - If we've seen this name with a different team, check if that player
      already has this team in their teams list (i.e. they moved clubs).
      If so, use that key.
    - Otherwise create a new key for this name+team combo.
    """
    # Collect all existing entries for this name
    matching_keys = [k for k in players_map if k == name or
                      k.startswith(f"{name}|")]

    if not matching_keys:
        # First time we see this name — use name|team as key
        return f"{name}|{team}" if team else name

    # Check if any existing entry already has this team
    for key in matching_keys:
        p = players_map[key]
        if team in p["teams"]:
            return key

    # Check if there's only one entry and it has no team yet
    if len(matching_keys) == 1:
        p = players_map[matching_keys[0]]
        if not p["teams"]:
            return matching_keys[0]

    # This name+team combo hasn't been seen before
    # It could be the same player at a new club, or a different player
    # Use name|team as a new unique key
    new_key = f"{name}|{team}" if team else name

    # If that key already exists (shouldn't normally happen), make it unique
    counter = 2
    base_key = new_key
    while new_key in players_map:
        new_key = f"{base_key}_{counter}"
        counter += 1

    return new_key

# Track which player key a name+team maps to so cards can find the right
# player even when card events don't always have team info
name_team_to_key = {}

def get_or_create_player(players_map, name, team, season):
    key = find_player_key(players_map, name, team)
    if key not in players_map:
        players_map[key] = make_player(name)
    # Cache this name+team -> key mapping
    if team:
        name_team_to_key[(name, team)] = key
    return players_map[key], key

def get_or_create_player_season(player, season, team):
    for s in player["season_stats"]:
        if s["season"] == season:
            return s
    entry = {
        "season": season,
        "team": team,
        "goals": 0,
        "penalties": 0,
        "own_goals": 0,
        "yellow_cards": 0,
        "red_cards": 0,
        "goals_by_opponent": {}
    }
    player["season_stats"].append(entry)
    return entry

def add_team_if_missing(player, team):
    if team and team not in player["teams"]:
        player["teams"].append(team)

def add_season_if_missing(player, season):
    if season and season not in player["seasons"]:
        player["seasons"].append(season)

# ── Main ──────────────────────────────────────────────────────────────────
def main():
    match_files = collect_json_files(MATCHES_DIR)
    print(f"📂 Found {len(match_files)} match file(s) in {MATCHES_DIR}\n")

    players_map = {}
    teams_set = set()
    team_stats_map = {}

    for file_path in match_files:
        try:
            with open(file_path, encoding="utf-8") as f:
                match = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"⚠️  Skipping invalid file: {file_path} ({e})")
            continue

        season = season_from_path(file_path)
        home_team = (match.get("home_team") or "").strip()
        away_team = (match.get("away_team") or "").strip()
        home_score = match.get("home_score") or 0
        away_score = match.get("away_score") or 0

        teams_set.add(home_team)
        teams_set.add(away_team)

        # ── Team stats ────────────────────────────────────────────────────
        for team, scored, conceded in [
            (home_team, home_score, away_score),
            (away_team, away_score, home_score),
        ]:
            s = get_or_create_team_stats(team_stats_map, team, season)
            s["played"] += 1
            s["goals_for"] += scored
            s["goals_against"] += conceded
            if scored > conceded:
                s["wins"] += 1
                s["points"] += 3
            elif scored == conceded:
                s["draws"] += 1
                s["points"] += 1
            else:
                s["losses"] += 1
            if conceded == 0:
                s["clean_sheets"] += 1

        # ── Yellow cards ──────────────────────────────────────────────────
        for card in match.get("yellow_cards") or []:
            team = (card.get("team") or "").strip()
            name = (card.get("player") or "").strip()
            if team:
                s = get_or_create_team_stats(team_stats_map, team, season)
                s["yellow_cards"] += 1
            if name:
                p, key = get_or_create_player(players_map, name, team, season)
                add_team_if_missing(p, team)
                add_season_if_missing(p, season)
                p["yellow_cards"] += 1
                ps = get_or_create_player_season(p, season, team)
                ps["yellow_cards"] += 1

        # ── Red cards ─────────────────────────────────────────────────────
        for card in match.get("red_cards") or []:
            team = (card.get("team") or "").strip()
            name = (card.get("player") or "").strip()
            if team:
                s = get_or_create_team_stats(team_stats_map, team, season)
                s["red_cards"] += 1
            if name:
                p, key = get_or_create_player(players_map, name, team, season)
                add_team_if_missing(p, team)
                add_season_if_missing(p, season)
                p["red_cards"] += 1
                ps = get_or_create_player_season(p, season, team)
                ps["red_cards"] += 1

        # ── Scorers ───────────────────────────────────────────────────────
        for scorer in match.get("scorers") or []:
            name = (scorer.get("player") or "").strip()
            team = (scorer.get("team") or "").strip()
            if not name:
                continue

            if team == home_team:
                opponent = away_team
            elif team == away_team:
                opponent = home_team
            else:
                opponent = ""

            p, key = get_or_create_player(players_map, name, team, season)
            add_team_if_missing(p, team)
            add_season_if_missing(p, season)
            ps = get_or_create_player_season(p, season, team)

            if scorer.get("own_goal"):
                p["own_goals"] += 1
                ps["own_goals"] += 1
            elif scorer.get("penalty"):
                p["penalties"] += 1
                p["goals"] += 1
                ps["penalties"] += 1
                ps["goals"] += 1
                if opponent:
                    ps["goals_by_opponent"][opponent] = \
                        ps["goals_by_opponent"].get(opponent, 0) + 1
            else:
                p["goals"] += 1
                ps["goals"] += 1
                if opponent:
                    ps["goals_by_opponent"][opponent] = \
                        ps["goals_by_opponent"].get(opponent, 0) + 1

    # ── Finalise goal difference ────────────────────────────────────────────
    for s in team_stats_map.values():
        s["goal_difference"] = s["goals_for"] - s["goals_against"]

    # ── Sort season_stats by season for each player ─────────────────────────
    for p in players_map.values():
        p["season_stats"].sort(key=lambda s: s["season"])

    # ── Build output arrays ───────────────────────────────────────────────
    players = sorted(players_map.values(), key=lambda p: p["name"])
    teams = [{"name": t} for t in sorted(teams_set) if t]
    team_stats = sorted(
        team_stats_map.values(),
        key=lambda s: (s["season"], s["team"])
    )

    # ── Write output files ────────────────────────────────────────────────
    print()
    write_json(OUT_DIR / "players.json", players)
    write_json(OUT_DIR / "teams.json", teams)
    write_json(OUT_DIR / "team-stats.json", team_stats)

    print(f"\n🏆 Done! {len(match_files)} matches → {len(players)} players, {len(teams)} teams.")

if __name__ == "__main__":
    main()
