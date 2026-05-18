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
# Script lives in scripts/ — resolve repo root one level up
REPO_ROOT   = Path(__file__).parent.parent
MATCHES_DIR = REPO_ROOT / "docs" / "data" / "epl" / "matches"
OUT_DIR     = REPO_ROOT / "docs" / "data" / "epl"


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
    }


def get_or_create_team_stats(team_stats_map, team, season):
    key = f"{team}|{season}"
    if key not in team_stats_map:
        team_stats_map[key] = make_team_stats(team, season)
    return team_stats_map[key]


def get_or_create_player(players_map, name):
    if name not in players_map:
        players_map[name] = make_player(name)
    return players_map[name]


def add_team_if_missing(player, team):
    if team and team not in player["teams"]:
        player["teams"].append(team)


def add_season_if_missing(player, season):
    if season and season not in player["seasons"]:
        player["seasons"].append(season)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    match_files = collect_json_files(MATCHES_DIR)
    print(f"📂  Found {len(match_files)} match file(s) in {MATCHES_DIR}\n")

    players_map    = {}
    teams_set      = set()
    team_stats_map = {}

    for file_path in match_files:
        try:
            with open(file_path, encoding="utf-8") as f:
                match = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"⚠️   Skipping invalid file: {file_path} ({e})")
            continue

        season     = season_from_path(file_path)
        home_team  = (match.get("home_team") or "").strip()
        away_team  = (match.get("away_team") or "").strip()
        home_score = match.get("home_score") or 0
        away_score = match.get("away_score") or 0

        teams_set.add(home_team)
        teams_set.add(away_team)

        # ── Team stats: wins/draws/losses/goals ───────────────────────────────
        for team, scored, conceded in [
            (home_team, home_score, away_score),
            (away_team, away_score, home_score),
        ]:
            s = get_or_create_team_stats(team_stats_map, team, season)
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

        # ── Yellow cards ──────────────────────────────────────────────────────
        for card in match.get("yellow_cards") or []:
            team = (card.get("team") or "").strip()
            name = (card.get("player") or "").strip()

            # Team stats
            if team:
                s = get_or_create_team_stats(team_stats_map, team, season)
                s["yellow_cards"] += 1

            # Player stats
            if name:
                p = get_or_create_player(players_map, name)
                add_team_if_missing(p, team)
                add_season_if_missing(p, season)
                p["yellow_cards"] += 1

        # ── Red cards ─────────────────────────────────────────────────────────
        for card in match.get("red_cards") or []:
            team = (card.get("team") or "").strip()
            name = (card.get("player") or "").strip()

            # Team stats
            if team:
                s = get_or_create_team_stats(team_stats_map, team, season)
                s["red_cards"] += 1

            # Player stats
            if name:
                p = get_or_create_player(players_map, name)
                add_team_if_missing(p, team)
                add_season_if_missing(p, season)
                p["red_cards"] += 1

        # ── Scorers ───────────────────────────────────────────────────────────
        for scorer in match.get("scorers") or []:
            name = (scorer.get("player") or "").strip()
            team = (scorer.get("team") or "").strip()
            if not name:
                continue

            p = get_or_create_player(players_map, name)
            add_team_if_missing(p, team)
            add_season_if_missing(p, season)

            if scorer.get("own_goal"):
                p["own_goals"] += 1
            elif scorer.get("penalty"):
                p["penalties"] += 1
            else:
                p["goals"] += 1

    # ── Finalise goal difference ──────────────────────────────────────────────
    for s in team_stats_map.values():
        s["goal_difference"] = s["goals_for"] - s["goals_against"]

    # ── Build output arrays ───────────────────────────────────────────────────
    players    = sorted(players_map.values(), key=lambda p: p["name"])
    teams      = [{"name": t} for t in sorted(teams_set) if t]
    team_stats = sorted(
        team_stats_map.values(),
        key=lambda s: (s["season"], s["team"])
    )

    # ── Write output files ────────────────────────────────────────────────────
    print()
    write_json(OUT_DIR / "players.json",    players)
    write_json(OUT_DIR / "teams.json",      teams)
    write_json(OUT_DIR / "team-stats.json", team_stats)

    print(f"\n🏆  Done! {len(match_files)} matches → {len(players)} players, {len(teams)} teams.")


if __name__ == "__main__":
    main()
