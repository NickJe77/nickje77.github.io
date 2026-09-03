#!/usr/bin/env python3
"""
build_mls_data.py

Reads all match JSON files from docs/data/mls/matches/<season>/*.json
and generates four output files:
  - docs/data/mls/players.json
  - docs/data/mls/teams.json
  - docs/data/mls/team-stats.json
  - docs/data/mls/match-records.json

MLS runs a single-calendar-year season (e.g. "2024"), not the split-year
format used by European leagues ("2024-2025") -- season identity here is
whatever folder name sits directly under matches/, so this just works as
long as match files are organised as matches/2024/*.json, matches/2025/*.json,
etc. No season-format-specific logic needed in this script at all.

Place this file in the scripts/ folder.
Run from the root of your GitHub repo (nickje77.github.io/)
"""

import json
import re
import sys
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
REPO_ROOT   = Path(__file__).parent.parent
MATCHES_DIR = REPO_ROOT / "docs" / "data" / "mls" / "matches"
OUT_DIR     = REPO_ROOT / "docs" / "data" / "mls"

# ── Team name canonicalization ───────────────────────────────────────────────
# Raw match data can use different names/abbreviations for the same real
# club (confirmed real cases elsewhere: PSG/Paris Saint-Germain in Ligue 1,
# Bailey Williams in AFL). Left unmapped, that splits one real team into two
# separate identities across every page that reads team names. Empty for
# now -- add entries here the moment a real MLS collision is found (e.g. if
# raw data uses "LAFC" alongside "Los Angeles FC", or "NYCFC" alongside
# "New York City FC"), the same way it was done for Ligue 1's PSG case.
TEAM_NAME_CANONICAL = {
    # "lafc": "Los Angeles FC",
    # "nycfc": "New York City FC",
}


def canonical_team(name):
    name = (name or "").strip()
    if not name:
        return name
    return TEAM_NAME_CANONICAL.get(name.lower(), name)


# ── Helpers ───────────────────────────────────────────────────────────────────

def collect_json_files(directory: Path) -> list:
    if not directory.exists():
        print(f"❌  Matches directory not found: {directory}", file=sys.stderr)
        sys.exit(1)
    return sorted(directory.rglob("*.json"))


def season_from_path(file_path: Path) -> str:
    """Returns the single-year season identifier (e.g. "2024") used
    throughout the site's output. The raw match folders on disk are
    still split-year named ("2024-2025") -- that's the real, unchanged
    upload structure -- but MLS runs a single-calendar-year season, so
    everything derived from these files (players.json, teams.json,
    team-stats.json, match-records.json) uses just the first year.
    """
    parts = file_path.parts
    try:
        idx = list(parts).index("matches")
        folder_name = parts[idx + 1]
    except (ValueError, IndexError):
        return "unknown"

    m = re.match(r"^(\d{4})-\d{4}$", folder_name)
    if m:
        return m.group(1)
    return folder_name


def split_year_folder(single_year: str) -> str:
    """The inverse: given a single-year season identifier like "2024",
    returns the actual split-year folder/file name on disk ("2024-2025").
    Used only by scripts/pages that need to fetch the raw source files
    directly, not the build script's own aggregate outputs.
    """
    if re.match(r"^\d{4}$", single_year):
        return f"{single_year}-{int(single_year)+1}"
    return single_year


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


def get_or_create_player(players_map, name, team, season):
    """Always key by name alone — one record per player regardless of club."""
    if name not in players_map:
        players_map[name] = make_player(name)
    return players_map[name]


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


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    match_files = collect_json_files(MATCHES_DIR)
    print(f"📂  Found {len(match_files)} match file(s) in {MATCHES_DIR}\n")

    players_map     = {}
    teams_set       = set()
    team_stats_map  = {}
    match_summaries = []  # feeds match-records.json (biggest wins, highest scoring)

    for file_path in match_files:
        try:
            with open(file_path, encoding="utf-8") as f:
                match = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"⚠️   Skipping invalid file: {file_path} ({e})")
            continue

        season     = season_from_path(file_path)
        home_team  = canonical_team(match.get("home_team"))
        away_team  = canonical_team(match.get("away_team"))
        home_score = match.get("home_score") or 0
        away_score = match.get("away_score") or 0

        if not home_team or not away_team:
            continue

        match_summaries.append({
            "home_team": home_team, "away_team": away_team,
            "home_score": home_score, "away_score": away_score,
            "season": season,
        })

        teams_set.add(home_team)
        teams_set.add(away_team)

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

        for card in match.get("yellow_cards") or []:
            team = canonical_team(card.get("team"))
            name = (card.get("player") or "").strip()

            if team:
                s = get_or_create_team_stats(team_stats_map, team, season)
                s["yellow_cards"] += 1

            if name:
                p = get_or_create_player(players_map, name, team, season)
                add_team_if_missing(p, team)
                add_season_if_missing(p, season)
                p["yellow_cards"] += 1
                ps = get_or_create_player_season(p, season, team)
                ps["yellow_cards"] += 1

        for card in match.get("red_cards") or []:
            team = canonical_team(card.get("team"))
            name = (card.get("player") or "").strip()

            if team:
                s = get_or_create_team_stats(team_stats_map, team, season)
                s["red_cards"] += 1

            if name:
                p = get_or_create_player(players_map, name, team, season)
                add_team_if_missing(p, team)
                add_season_if_missing(p, season)
                p["red_cards"] += 1
                ps = get_or_create_player_season(p, season, team)
                ps["red_cards"] += 1

        for scorer in match.get("scorers") or []:
            name = (scorer.get("player") or "").strip()
            team = canonical_team(scorer.get("team"))
            if not name:
                continue

            if team == home_team:
                opponent = away_team
            elif team == away_team:
                opponent = home_team
            else:
                opponent = ""

            p = get_or_create_player(players_map, name, team, season)
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
                    ps["goals_by_opponent"][opponent] = ps["goals_by_opponent"].get(opponent, 0) + 1
            else:
                p["goals"] += 1
                ps["goals"] += 1
                if opponent:
                    ps["goals_by_opponent"][opponent] = ps["goals_by_opponent"].get(opponent, 0) + 1

    for s in team_stats_map.values():
        s["goal_difference"] = s["goals_for"] - s["goals_against"]

    for p in players_map.values():
        p["season_stats"].sort(key=lambda s: s["season"])

    players    = sorted(players_map.values(), key=lambda p: p["name"])
    teams      = [{"name": t} for t in sorted(teams_set) if t]
    team_stats = sorted(
        team_stats_map.values(),
        key=lambda s: (s["season"], s["team"])
    )

    # ── Match records (biggest wins, highest scoring) ─────────────────────────
    biggest_wins = sorted(
        match_summaries,
        key=lambda g: abs(g["home_score"] - g["away_score"]),
        reverse=True,
    )[:25]
    highest_scoring = sorted(
        match_summaries,
        key=lambda g: g["home_score"] + g["away_score"],
        reverse=True,
    )[:25]
    match_records = {
        "biggest_wins": biggest_wins,
        "highest_scoring": highest_scoring,
    }

    print()
    write_json(OUT_DIR / "players.json",       players)
    write_json(OUT_DIR / "teams.json",         teams)
    write_json(OUT_DIR / "team-stats.json",    team_stats)
    write_json(OUT_DIR / "match-records.json", match_records)

    print(f"\n🏆  Done! {len(match_files)} matches → {len(players)} players, {len(teams)} teams.")


if __name__ == "__main__":
    main()
