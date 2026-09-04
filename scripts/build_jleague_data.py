#!/usr/bin/env python3
"""
build_jleague_data.py

Reads all match JSON files from docs/data/jleague/matches/<season>/*.json
and generates four output files:
  - docs/data/jleague/players.json
  - docs/data/jleague/teams.json
  - docs/data/jleague/team-stats.json
  - docs/data/jleague/match-records.json

J-League uses a genuinely different, much richer raw match schema than
every other competition on this site (Ligue 1, Bundesliga, A-League,
MLS all use a flat structure: home_team/away_team as plain strings,
home_score/away_score as integers, separate top-level scorers/
yellow_cards/red_cards arrays). This data instead has:

  - match.home_team / match.away_team as NESTED OBJECTS (team_id, slug,
    name) -- the team name is match.home_team.name, not match.home_team.
  - match.final_score as a COLON-SEPARATED STRING ("0:2"), not separate
    integer fields.
  - Goals tracked via a top-level "events" array (type == "goal"), using
    "scorer" (player name) and "side" ("home"/"away") -- there is no
    separate "scorers" list.
  - Cards NOT tracked as a flat list at all -- they're embedded per
    player inside lineups.home/away.starters[] and .bench[], each
    player having "yellow_card_minutes" and "red_card_minutes" as
    ARRAYS (length = number of that card in this match).

Confirmed by checking every event across the full ~10,300 file dataset:
there is no penalty or own-goal flag anywhere in this data (event keys
are only scorer/slug/person_id/minute/side/running_score/type, and
"type" is always exactly "goal"). Penalties/own goals are therefore
always recorded as 0 here -- that's an honest limitation of the source
data, not a bug in this script. If a future upload of this data adds
that distinction, this is the only place that needs updating.

Place this file in the scripts/ folder.
Run from the root of your GitHub repo (nickje77.github.io/)
"""

import json
import sys
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
REPO_ROOT   = Path(__file__).parent.parent
MATCHES_DIR = REPO_ROOT / "docs" / "data" / "jleague" / "matches"
OUT_DIR     = REPO_ROOT / "docs" / "data" / "jleague"

# ── Team name canonicalization ───────────────────────────────────────────────
# Empty for now -- add entries here the moment a real J-League name
# collision is found (same pattern already used for Ligue 1's PSG case
# and confirmed real collisions in AFL), rather than guessing at ones
# that might not exist in this data.
TEAM_NAME_CANONICAL = {}


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


def parse_final_score(score_str):
    """'0:2' -> (0, 2). Returns (None, None) if the score is missing or
    malformed (e.g. a postponed/abandoned match with no result)."""
    if not score_str or ":" not in score_str:
        return None, None
    try:
        home, away = score_str.split(":", 1)
        return int(home.strip()), int(away.strip())
    except (ValueError, TypeError):
        return None, None


def make_team_stats(team, season):
    return {
        "team": team, "season": season,
        "played": 0, "wins": 0, "draws": 0, "losses": 0,
        "goals_for": 0, "goals_against": 0, "goal_difference": 0,
        "points": 0, "clean_sheets": 0, "yellow_cards": 0, "red_cards": 0,
    }


def make_player(name):
    return {
        "name": name, "teams": [], "seasons": [],
        "goals": 0, "penalties": 0, "own_goals": 0,
        "yellow_cards": 0, "red_cards": 0, "season_stats": [],
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


def get_or_create_player_season(player, season, team):
    for s in player["season_stats"]:
        if s["season"] == season and s["team"] == team:
            return s
    entry = {
        "season": season, "team": team,
        "goals": 0, "penalties": 0, "own_goals": 0,
        "yellow_cards": 0, "red_cards": 0, "goals_by_opponent": {},
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

    skipped_no_score = 0

    for file_path in match_files:
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"⚠️   Skipping invalid file: {file_path} ({e})")
            continue

        season = season_from_path(file_path)
        match  = data.get("match", {})

        home_team = canonical_team((match.get("home_team") or {}).get("name"))
        away_team = canonical_team((match.get("away_team") or {}).get("name"))
        home_score, away_score = parse_final_score(match.get("final_score"))

        if not home_team or not away_team:
            continue
        if home_score is None or away_score is None:
            # Match hasn't been played yet / no result recorded -- can't
            # count it toward stats, but it's not an error.
            skipped_no_score += 1
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
                s["wins"] += 1; s["points"] += 3
            elif scored == conceded:
                s["draws"] += 1; s["points"] += 1
            else:
                s["losses"] += 1
            if conceded == 0:
                s["clean_sheets"] += 1

        # ── Goals -- from the top-level "events" array ───────────────────
        for event in data.get("events", []):
            if event.get("type") != "goal":
                continue
            name = (event.get("scorer") or "").strip()
            if not name:
                continue
            side = event.get("side")
            team = home_team if side == "home" else away_team if side == "away" else ""
            opponent = away_team if team == home_team else home_team if team else ""

            p = get_or_create_player(players_map, name)
            add_team_if_missing(p, team)
            add_season_if_missing(p, season)
            ps = get_or_create_player_season(p, season, team)

            # No penalty/own-goal flag exists in this data source at all
            # (confirmed across every file) -- every goal event is
            # counted as a plain goal.
            p["goals"] += 1
            ps["goals"] += 1
            if opponent:
                ps["goals_by_opponent"][opponent] = ps["goals_by_opponent"].get(opponent, 0) + 1

        # ── Cards -- embedded per player inside lineups, not a flat list ─
        lineups = data.get("lineups", {})
        for side_key, team in (("home", home_team), ("away", away_team)):
            side_data = lineups.get(side_key, {})
            all_players = (side_data.get("starters") or []) + (side_data.get("bench") or [])
            for player_entry in all_players:
                name = (player_entry.get("name") or "").strip()
                if not name:
                    continue
                yellows = len(player_entry.get("yellow_card_minutes") or [])
                reds    = len(player_entry.get("red_card_minutes") or [])
                if yellows == 0 and reds == 0:
                    continue

                p = get_or_create_player(players_map, name)
                add_team_if_missing(p, team)
                add_season_if_missing(p, season)
                ps = get_or_create_player_season(p, season, team)

                if yellows:
                    p["yellow_cards"] += yellows
                    ps["yellow_cards"] += yellows
                    s = get_or_create_team_stats(team_stats_map, team, season)
                    s["yellow_cards"] += yellows
                if reds:
                    p["red_cards"] += reds
                    ps["red_cards"] += reds
                    s = get_or_create_team_stats(team_stats_map, team, season)
                    s["red_cards"] += reds

    for s in team_stats_map.values():
        s["goal_difference"] = s["goals_for"] - s["goals_against"]

    for p in players_map.values():
        p["season_stats"].sort(key=lambda s: s["season"])

    players    = sorted(players_map.values(), key=lambda p: p["name"])
    teams      = [{"name": t} for t in sorted(teams_set) if t]
    team_stats = sorted(team_stats_map.values(), key=lambda s: (s["season"], s["team"]))

    biggest_wins = sorted(
        match_summaries, key=lambda g: abs(g["home_score"] - g["away_score"]), reverse=True
    )[:25]
    highest_scoring = sorted(
        match_summaries, key=lambda g: g["home_score"] + g["away_score"], reverse=True
    )[:25]
    match_records = {"biggest_wins": biggest_wins, "highest_scoring": highest_scoring}

    print()
    write_json(OUT_DIR / "players.json",       players)
    write_json(OUT_DIR / "teams.json",         teams)
    write_json(OUT_DIR / "team-stats.json",    team_stats)
    write_json(OUT_DIR / "match-records.json", match_records)

    print(f"\nSkipped (no final score recorded): {skipped_no_score}")
    print(f"🏆  Done! {len(match_files) - skipped_no_score} matches → {len(players)} players, {len(teams)} teams.")


if __name__ == "__main__":
    main()
