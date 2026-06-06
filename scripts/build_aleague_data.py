#!/usr/bin/env python3
"""
build_aleague_data.py

Reads all match JSON files from docs/data/aleague/matches/<season>/*.json
and generates three output files:
  - docs/data/aleague/players.json
  - docs/data/aleague/teams.json
  - docs/data/aleague/team-stats.json

Place this file in the scripts/ folder.
Run from the root of your GitHub repo.
"""

import json
import sys
from pathlib import Path

REPO_ROOT   = Path(__file__).parent.parent
MATCHES_DIR = REPO_ROOT / "docs" / "data" / "aleague" / "matches"
OUT_DIR     = REPO_ROOT / "docs" / "data" / "aleague"

# Normalise historical name changes at data level
TEAM_NAME_MAP = {
    "Queensland Roar": "Brisbane Roar",
    "Melbourne Heart": "Melbourne City",
}

def normalise_team(name):
    if not name:
        return ""
    return TEAM_NAME_MAP.get(name.strip(), name.strip())

def collect_json_files(directory):
    if not directory.exists():
        print(f"Matches directory not found: {directory}", file=sys.stderr)
        sys.exit(1)
    return sorted(directory.rglob("*.json"))

def season_from_path(file_path):
    parts = file_path.parts
    try:
        idx = list(parts).index("matches")
        return parts[idx + 1]
    except (ValueError, IndexError):
        return "unknown"

def write_json(file_path, data):
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Written: {file_path}")

def make_team_stats(team, season):
    return {"team":team,"season":season,"played":0,"wins":0,"draws":0,"losses":0,
            "goals_for":0,"goals_against":0,"goal_difference":0,"points":0,
            "clean_sheets":0,"yellow_cards":0,"red_cards":0}

def make_player(name):
    return {"name":name,"teams":[],"seasons":[],"appearances":0,"goals":0,
            "penalties":0,"own_goals":0,"yellow_cards":0,"red_cards":0,"season_stats":[]}

def get_or_create_team_stats(m, team, season):
    key = f"{team}|{season}"
    if key not in m:
        m[key] = make_team_stats(team, season)
    return m[key]

def get_or_create_player(m, name):
    if name not in m:
        m[name] = make_player(name)
    return m[name]

def get_or_create_player_season(player, season, team):
    for s in player["season_stats"]:
        if s["season"] == season and s["team"] == team:
            return s
    entry = {"season":season,"team":team,"goals":0,"penalties":0,"own_goals":0,
             "yellow_cards":0,"red_cards":0,"goals_by_opponent":{}}
    player["season_stats"].append(entry)
    return entry

def add_team_if_missing(player, team):
    if team and team not in player["teams"]:
        player["teams"].append(team)

def add_season_if_missing(player, season):
    if season and season not in player["seasons"]:
        player["seasons"].append(season)

def get_name(d):
    name = d.get("player") or d.get("name") or ""
    return " ".join(str(name).split())

def main():
    match_files = collect_json_files(MATCHES_DIR)
    print(f"Found {len(match_files)} match files\n")

    players_map    = {}
    teams_set      = set()
    team_stats_map = {}
    skipped = 0
    goals_counted = 0
    own_goals_counted = 0

    for file_path in match_files:
        try:
            with open(file_path, encoding="utf-8") as f:
                match = json.load(f)
        except Exception as e:
            print(f"Skipping {file_path}: {e}")
            skipped += 1
            continue

        season    = season_from_path(file_path)
        home_team = normalise_team(match.get("home_team") or "")
        away_team = normalise_team(match.get("away_team") or "")
        home_score = match.get("home_score") or 0
        away_score = match.get("away_score") or 0

        if not home_team or not away_team:
            skipped += 1
            continue

        teams_set.add(home_team)
        teams_set.add(away_team)

        for team, scored, conceded in [(home_team,home_score,away_score),(away_team,away_score,home_score)]:
            s = get_or_create_team_stats(team_stats_map, team, season)
            s["played"] += 1
            s["goals_for"] += scored
            s["goals_against"] += conceded
            if scored > conceded:
                s["wins"] += 1; s["points"] += 3
            elif scored == conceded:
                s["draws"] += 1; s["points"] += 1
            else:
                s["losses"] += 1
            if conceded == 0:
                s["clean_sheets"] += 1

        for scorer in (match.get("scorers") or []):
            name = get_name(scorer)
            if not name:
                continue
            team = normalise_team(scorer.get("team") or "")
            if not team:
                continue
            opponent = away_team if team == home_team else (home_team if team == away_team else "")
            p  = get_or_create_player(players_map, name)
            add_team_if_missing(p, team)
            add_season_if_missing(p, season)
            ps = get_or_create_player_season(p, season, team)
            if scorer.get("own_goal", False):
                p["own_goals"] += 1; ps["own_goals"] += 1; own_goals_counted += 1
            else:
                p["goals"] += 1; ps["goals"] += 1; goals_counted += 1
                if scorer.get("penalty", False):
                    p["penalties"] += 1; ps["penalties"] += 1
                if opponent:
                    ps["goals_by_opponent"][opponent] = ps["goals_by_opponent"].get(opponent, 0) + 1

        for card in (match.get("yellow_cards") or []):
            name = get_name(card)
            if not name: continue
            team = normalise_team(card.get("team") or "")
            if not team: continue
            p  = get_or_create_player(players_map, name)
            add_team_if_missing(p, team); add_season_if_missing(p, season)
            ps = get_or_create_player_season(p, season, team)
            p["yellow_cards"] += 1; ps["yellow_cards"] += 1
            get_or_create_team_stats(team_stats_map, team, season)["yellow_cards"] += 1

        for card in (match.get("red_cards") or []):
            name = get_name(card)
            if not name: continue
            team = normalise_team(card.get("team") or "")
            if not team: continue
            p  = get_or_create_player(players_map, name)
            add_team_if_missing(p, team); add_season_if_missing(p, season)
            ps = get_or_create_player_season(p, season, team)
            p["red_cards"] += 1; ps["red_cards"] += 1
            get_or_create_team_stats(team_stats_map, team, season)["red_cards"] += 1

    for s in team_stats_map.values():
        s["goal_difference"] = s["goals_for"] - s["goals_against"]

    for p in players_map.values():
        p["season_stats"].sort(key=lambda s: s["season"])

    players    = sorted(players_map.values(), key=lambda p: p["name"])
    teams      = [{"name": t} for t in sorted(teams_set) if t]
    team_stats = sorted(team_stats_map.values(), key=lambda s: (s["season"], s["team"]))

    print()
    write_json(OUT_DIR / "players.json",    players)
    write_json(OUT_DIR / "teams.json",      teams)
    write_json(OUT_DIR / "team-stats.json", team_stats)

    print(f"\nDone! {len(match_files)-skipped} matches, {len(players)} players, {goals_counted} goals, {own_goals_counted} own goals")

if __name__ == "__main__":
    main()
