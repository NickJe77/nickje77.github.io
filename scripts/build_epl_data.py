#!/usr/bin/env python3
"""
build_epl_data.py

Reads all match JSON files from docs/data/epl/matches/<season>/*.json
and generates three output files:
  - docs/data/epl/players.json
  - docs/data/epl/teams.json
  - docs/data/epl/team-stats.json

Place this file in the scripts/ folder.
Run from the root of your GitHub repo (nickje77.github.io/)
"""

import json
import sys
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
REPO_ROOT   = Path(__file__).parent.parent
MATCHES_DIR = REPO_ROOT / "docs" / "data" / "epl" / "matches"
OUT_DIR     = REPO_ROOT / "docs" / "data" / "epl"

# Players who are known to share a name — map "name|team" to a unique key
# Add more here as needed
SAME_NAME_PLAYERS = {
    # "Alan Smith" the striker started at Leeds, "Alan Smith" the midfielder at Arsenal
    # We differentiate by first team
}

# Max season gap before treating same-name player as a different person
MAX_SEASON_GAP = 4


# ── Helpers ───────────────────────────────────────────────────────────────────

def collect_json_files(directory: Path) -> list:
    if not directory.exists():
        print(f"❌  Matches directory not found: {directory}", file=sys.stderr)
        sys.exit(1)
    return sorted(directory.rglob("*.json"))


def season_from_path(file_path: Path) -> str:
    parts = file_path.parts
    try:
        idx = list(parts).index("matches")
        return parts[idx + 1]
    except (ValueError, IndexError):
        return "unknown"


def season_start_year(season: str) -> int:
    try:
        return int(season.split("-")[0])
    except (ValueError, IndexError):
        return 0


def write_json(file_path: Path, data):
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅  Written: {file_path}")


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


def find_player_key(players_map, name, team, season):
    """
    Find the right player entry for this name+team+season combination.
    If a player with this name exists but has a large season gap, create a new entry.
    """
    season_year = season_start_year(season)

    # Collect all existing entries for this name
    matching_keys = [k for k in players_map if k == name or k.startswith(f"{name}|")]

    if not matching_keys:
        return name

    # Check each existing entry to see
