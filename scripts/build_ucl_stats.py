#!/usr/bin/env python3
import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT   = Path(os.environ.get("GITHUB_WORKSPACE", str(Path(__file__).parent.parent)))
MATCHES_DIR = REPO_ROOT / "docs" / "data" / "ucl" / "matches"
OUT_DIR     = REPO_ROOT / "docs" / "data" / "ucl"

TEAM_NAME_MAP = {
    "Man Utd":                    "Manchester United",
    "Man United":                 "Manchester United",
    "B. Dortmund":                "Borussia Dortmund",
    "Dortmund":                   "Borussia Dortmund",
    "Bayern":                     "Bayern Munich",
    "FC Bayern":                  "Bayern Munich",
    "FC Bayern Munich":           "Bayern Munich",
    "B. Munich":                  "Bayern Munich",
    "Paris":                      "Paris Saint-Germain",
    "PSG":                        "Paris Saint-Germain",
    "Inter":                      "Internazionale",
    "Inter Milan":                "Internazionale",
    "FC Internazionale":          "Internazionale",
    "Atletico":                   "Atletico Madrid",
    "Atletico Madrid":            "Atletico Madrid",
    "S. Bratislava":              "Slovan Bratislava",
    "Crvena Zvezda":              "Red Star Belgrade",
    "FK Crvena zvezda":           "Red Star Belgrade",
    "Milan":                      "AC Milan",
    "Juventus FC":                "Juventus",
    "FCB":                        "Barcelona",
    "FC Barcelona":               "Barcelona",
    "Real":                       "Real Madrid",
    "FC Porto":                   "Porto",
    "FC Valencia":                "Valencia",
    "Bayer Leverkusen":           "Leverkusen",
    "Bayer 04":                   "Leverkusen",
    "Olympique Lyon":             "Lyon",
    "Olympique de Marseille":     "Marseille",
    "AS Roma":                    "Roma",
    "SS Lazio":                   "Lazio",
    "ACF Fiorentina":             "Fiorentina",
    "AFC Ajax":                   "Ajax",
    "PSV":                        "PSV Eindhoven",
    "Sporting":                   "Sporting CP",
    "Sporting Lisbon":            "Sporting CP",
    "Zenit":                      "Zenit St. Petersburg",
    "RB Salzburg":                "Red Bull Salzburg",
    "Shakhtar":                   "Shakhtar Donetsk",
    "Celtic FC":                  "Celtic",
    "Rangers FC":                 "Rangers",
    "SL Benfica":                 "Benfica",
    "Galatasaray SK":             "Galatasaray",
    "Club Brugge KV":             "Club Brugge",
}

def normalise_team(name: str) -> str:
    name = (name or "").strip()
    return TEAM_NAME_MAP.get(name, name)

def collect_json_files(directory: Path) -> list:
    if not directory.exists():
        print(f"Matches directory not found: {directory}", file=sys.stderr)
        sys.exit(1)
    return sorted(directory.rglob("*.json"))

def season_from_path(file_path: Path) -> str:
    parts = file_path.parts
    try:
        idx = list(parts).index("matches")
        raw = parts[idx + 1]
        match_obj = re.match(r'^(\d{4})-\d*(\d{2})$', raw)
        if match_obj:
            raw = match_obj.group(1) + "-" + match_obj.group(2)
        return raw
    except (ValueError, IndexError):
        return "unknown"

def build_lineup_map(match: dict, home_team: str, away_team: str) -> dict:
    lineup_map = {}
    for player in match.get("home_lineup") or []:
        if player:
            lineup_map[player.strip()] = home_team
    for player in match.get("away_lineup") or []:
        if player:
            lineup_map[player.strip()] = away_team
    return lineup_map

def resolve_team(raw_team: str, player_name: str, home_team: str, away_team: str,
                 lineup_map: dict, known_teams: dict) -> str:
    t = normalise_team(raw_team)
    if t:
        return t
    if player_name in lineup_map:
        return lineup_map[player_name]
    if player_name in known_teams:
        prev = known_teams[player_name]
        if prev == home_team or prev == away_team:
            return prev
    return ""

def write_json(file_path: Path, data):
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Written: {file_path}")

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
    matching_keys = [k for k in players_map if k == name or k.startswith(f"{name}|")]
    if not matching_keys:
        return f"{name}|{team}" if team else name
    for key in matching_keys:
        p = players_map[key]
        if team in p["teams"]:
            return key
    return matching_keys[0]

def get_or_create_player(players_map, name, team, season):
    key = find_player_key(players_map, name, team)
    if key not in players_map:
        players_map[key] = make_player(name)
    return players_map[key], key

def get_or_create_player_season(player, season, team):
    for s in player["season_stats"]:
        if s["season"] == season and s["team"] == team:
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

def main():
    match_files = collect_json_files(MATCHES_DIR)
    print(f"Found {len(match_files)} match files in {MATCHES_DIR}\n")

    players_map        = {}
    teams_set          = set()
    team_stats_map     = {}
    known_player_teams = {}

    for file_path in sorted(match_files):
        try:
            with open(file_path, encoding="utf-8") as f:
                match = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Skipping invalid file: {file_path} ({e})")
            continue

        season     = season_from_path(file_path)
        home_team  = normalise_team(match.get("home_team") or match.get("home") or "")
        away_team  = normalise_team(match.get("away_team") or match.get("away") or "")
        home_score = match.get("home_score") or 0
        away_score = match.get("away_score") or 0

        if not home_team or not away_team:
            continue

        teams_set.add(home_team)
        teams_set.add(away_team)

        lineup_map = build_lineup_map(match, home_team, away_team)

        for team, scored, conceded in [
            (home_team, home_score, away_score),
