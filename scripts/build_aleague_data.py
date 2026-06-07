#!/usr/bin/env python3
"""
build_aleague_data.py
Reads all match JSON files and generates players.json, teams.json, team-stats.json
Also rebuilds season JSONs with home, away, score_home, score_away fields
so the team page loads fast (same structure as EPL season JSONs).
Queensland Roar -> Brisbane Roar, Melbourne Heart -> Melbourne City at data level.
"""

import json
import sys
from pathlib import Path

REPO_ROOT   = Path(__file__).parent.parent
MATCHES_DIR = REPO_ROOT / "docs" / "data" / "aleague" / "matches"
SEASONS_DIR = REPO_ROOT / "docs" / "data" / "aleague" / "seasons"
OUT_DIR     = REPO_ROOT / "docs" / "data" / "aleague"

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

def rebuild_season_jsons(match_data):
    """
    Update season JSON files with home, away, score_home, score_away
    so the team page loads fast — same structure as EPL season JSONs.
    Uses match_data dict already built during main processing.
    """
    if not SEASONS_DIR.exists():
        return

    for season_file in sorted(SEASONS_DIR.glob("*.json")):
        season_id = season_file.stem
        try:
            with open(season_file, encoding="utf-8") as f:
                data = json.load(f)
        except:
            continue

        games = data.get("games", data) if isinstance(data, dict) else data
        updated = 0

        for game in games:
            match_id = game.get("match_id")
            if not match_id or match_id not in match_data:
                continue
            m = match_data[match_id]
            game["home"]       = m["home"]
            game["away"]       = m["away"]
            game["score_home"] = m["score_home"]
            game["score_away"] = m["score_away"]
            game["date"]       = m["date"]
            updated += 1

        if isinstance(data, dict):
            data["games"] = games
            out = data
        else:
            out = games

        with open(season_file, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, ensure_ascii=False)

        print(f"  Season {season_id}: {updated} games updated")

def main():
    match_files = collect_json_files(MATCHES_DIR)
    print(f"Found {len(match_files)} match files\n")

    seen_match_ids = set()
    players_map    = {}
    teams_set      = set()
    team_stats_map = {}
    match_data     = {}  # match_id -> {home, away, score_home, score_away, date}
    skipped        = 0
    duplicates     = 0
    goals_counted  = 0
    own_goals_counted = 0

    for file_path in match_files:
        try:
            with open(file_path, encoding="utf-8") as f:
                match = json.load(f)
        except Exception as e:
            print(f"Skipping {file_path}: {e}")
            skipped += 1
            continue

        match_id = match.get("match_id") or str(file_path)
        if match_id in seen_match_ids:
            duplicates += 1
            continue
        seen_match_ids.add(match_id)

        season    = season_from_path(file_path)
        home_team = normalise_team(match.get("home_team") or "")
        away_team = normalise_team(match.get("away_team") or "")
        home_score = match.get("home_score") or 0
        away_score = match.get("away_score") or 0

        if not home_team or not away_team:
            skipped += 1
            continue

        # Store for season JSON rebuild
        match_data[match_id] = {
            "home":       home_team,
            "away":       away_team,
            "score_home": home_score,
            "score_away": away_score,
            "date":       match.get("date", ""),
        }

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
            if not name: continue
            team = normalise_team(scorer.get("team") or "")
            if not team: continue
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

    print(f"\nRebuilding season JSONs...")
    rebuild_season_jsons(match_data)

    print(f"\nDone!")
    print(f"  {len(match_files)-skipped} matches processed")
    print(f"  {duplicates} duplicates skipped")
    print(f"  {skipped} files skipped")
    print(f"  {len(players)} players")
    print(f"  {goals_counted} goals, {own_goals_counted} own goals")

if __name__ == "__main__":
    main()
