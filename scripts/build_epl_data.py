#!/usr/bin/env python3
"""
build_epl_data.py

Reads all match JSON files from docs/data/epl/matches/<season>/*.json
and generates three output files:
  - docs/data/epl/players.json
  - docs/data/epl/teams.json
  - docs/data/epl/team-stats.json

Run from the root of your GitHub repo (nickje77.github.io/)
"""

import json
import os
import sys
from pathlib import Path
from collections import defaultdict

# ── Paths ─────────────────────────────────────────────────────────────────────
# Script lives in scripts/ but paths are relative to the repo root.
# GitHub Actions runs from the repo root, so these paths work as-is.
REPO_ROOT   = Path(__file__).parent.parent
MATCHES_DIR = REPO_ROOT / "docs/data/epl/matches"
OUT_DIR     = REPO_ROOT / "docs/data/epl"


# ── Helpers ───────────────────────────────────────────────────────────────────

def collect_json_files(directory: Path) -> list[Path]:
    """Recursively collect every .json file under a directory."""
    if not directory.exists():
        print(f"❌  Matches directory not found: {directory}", file=sys.stderr)
        sys.exit(1)
    return sorted(directory.rglob("*.json"))


def season_from_path(file_path: Path) -> str:
    """Derive a season string from the file path, e.g. '1993-1994'."""
    parts = file_path.parts
    try:
        matches_index = parts.index("matches")
        return parts[matches_index + 1]
    except (ValueError, IndexError):
        return "unknown"


def write_json(file_path: Path, data):
    """Write JSON to a file, creating directories as needed."""
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
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    match_files = collect_json_files(MATCHES_DIR)
    print(f"📂  Found {len(match_files)} match file(s) in {MATCHES_DIR}\n")

    players_map   = {}   # name → player record
    teams_set     = set()
    team_stats_map = {}  # "team|season" → stats record

    for file_path in match_files:
        try:
            with open(file_path, encoding="utf-8") as f:
                match = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"⚠️   Skipping invalid file: {file_path} ({e})")
            continue

        season     = season_from_path(file_path)
        home_team  = match.get("home_team", "")
        away_team  = match.get("away_team", "")
        home_score = match.get("home_score", 0) or 0
        away_score = match.get("away_score", 0) or 0

        # ── Register teams ────────────────────────────────────────────────────
        teams_set.add(home_team)
        teams_set.add(away_team)

        # ── Team stats ────────────────────────────────────────────────────────
        for team, scored, conceded in [
            (home_team, home_score, away_score),
            (away_team, away_score, home_score),
        ]:
            key = f"{team}|{season}"
            if key not in team_stats_map:
                team_stats_map[key] = make_team_stats(team, season)

            s = team_stats_map[key]
            s["played"]        += 1
            s["goals_for"]     += scored
            s["goals_against"] += conceded

            if scored > conceded:
                s["wins"]   += 1
                s["points"] += 3
            elif scored == conceded:
                s["draws"]  += 1
                s["points"] += 1
            else:
                s["losses"] += 1

            if conceded == 0:
                s["clean_sheets"] += 1

        # ── Cards per team ────────────────────────────────────────────────────
        for card in match.get("yellow_cards", []):
            key = f"{card.get('team', '')}|{season}"
            if key in team_stats_map:
                team_stats_map[key]["yellow_cards"] += 1

        for card in match.get("red_cards", []):
            key = f"{card.get('team', '')}|{season}"
            if key in team_stats_map:
                team_stats_map[key]["red_cards"] += 1

        # ── Players from scorers ──────────────────────────────────────────────
        for scorer in match.get("scorers", []):
            name = scorer.get("player", "").strip()
            team = scorer.get("team", "")
            if not name:
                continue

            if name not in players_map:
                players_map[name] = make_player(name)

            p = players_map[name]
            if team not in p["teams"]:
                p["teams"].append(team)
            if season not in p["seasons"]:
                p["seasons"].append(season)

            if scorer.get("own_goal"):
                p["own_goals"] += 1
            elif scorer.get("penalty"):
                p["penalties"] += 1
            else:
                p["goals"] += 1

        # ── Players from cards ────────────────────────────────────────────────
        for card in match.get("yellow_cards", []):
            name = card.get("player", "").strip()
            team = card.get("team", "")
            if not name:
                continue
            if name not in players_map:
                players_map[name] = make_player(name)
            p = players_map[name]
            if team not in p["teams"]:     p["teams"].append(team)
            if season not in p["seasons"]: p["seasons"].append(season)
            p["yellow_cards"] += 1

        for card in match.get("red_cards", []):
            name = card.get("player", "").strip()
            team = card.get("team", "")
            if not name:
                continue
            if name not in players_map:
                players_map[name] = make_player(name)
            p = players_map[name]
            if team not in p["teams"]:     p["teams"].append(team)
            if season not in p["seasons"]: p["seasons"].append(season)
            p["red_cards"] += 1

    # ── Finalise goal difference ──────────────────────────────────────────────
    for s in team_stats_map.values():
        s["goal_difference"] = s["goals_for"] - s["goals_against"]

    # ── Build output arrays ───────────────────────────────────────────────────
    players   = sorted(players_map.values(), key=lambda p: p["name"])
    teams     = [{"name": t} for t in sorted(teams_set)]
    team_stats = sorted(
        team_stats_map.values(),
        key=lambda s: (s["season"], s["team"])
    )

    # ── Write output files ────────────────────────────────────────────────────
    print()
    write_json(OUT_DIR / "players.json",    players)
    write_json(OUT_DIR / "teams.json",      teams)
    write_json(OUT_DIR / "team-stats.json", team_stats)

    print(f"\n🏆  Done! Processed {len(match_files)} matches → {len(players)} players, {len(teams)} teams.")


if __name__ == "__main__":
    main()
