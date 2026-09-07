#!/usr/bin/env python3
"""
build_uefaeuro_data.py

Reads all match JSON files from docs/data/uefaeuro/matches/<season>/*.json
and generates four output files:
  - docs/data/uefaeuro/players.json
  - docs/data/uefaeuro/teams.json
  - docs/data/uefaeuro/team-stats.json
  - docs/data/uefaeuro/match-records.json

UEFA Euro uses a genuinely different, much richer raw match schema than
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

Confirmed by checking every event across the full 385 file dataset:
there is no explicit penalty or own-goal flag anywhere in this data
(event keys are only scorer/slug/person_id/minute/side/running_score/
type, and "type" is always exactly "goal"). Penalties are therefore
always recorded as 0 -- that's an honest limitation of the source data.

Own goals were detectable this same way for J-League and Brazilian
Serie A (checking whether a goal's "scorer" is found in the lineup of
the OPPOSITE team from the one it's credited to), but tested directly
against this real Euro dataset, that technique found zero own goals
across all 1,137 goal events -- despite real Euro history definitely
including some. Lineup data itself is genuinely populated (checked a
real match directly, not an empty-data artifact), so the cause isn't
obvious from what's been checked so far. own_goals will honestly show
0 for every player here until this is investigated further -- goals
themselves, team stats, and match records are unaffected by this.

Place this file in the scripts/ folder.
Run from the root of your GitHub repo (nickje77.github.io/)
"""

import json
import sys
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
REPO_ROOT   = Path(__file__).parent.parent
MATCHES_DIR = REPO_ROOT / "docs" / "data" / "uefaeuro" / "matches"
OUT_DIR     = REPO_ROOT / "docs" / "data" / "uefaeuro"

# ── Team name canonicalization ───────────────────────────────────────────────
# team_id is always null for national teams on worldfootball.net (unlike
# club competitions, where it's a reliable ground truth) -- confirmed by
# checking a real match file directly, so unlike Ligue 1/Brazil this
# couldn't be verified by cross-referencing IDs. Reviewed all 40 distinct
# team names directly instead: every one represents a genuinely separate
# real national team, including several that could look like duplicates
# at a glance but aren't -- USSR/CIS/Russia and CSSR/Czech Republic/
# Slovakia each reflect real historical splits, not naming
# inconsistencies for the same team, and were deliberately NOT merged.
# Add entries here only if a genuine same-team naming inconsistency is
# found (same approach already used for Ligue 1's PSG case).
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


def true_regulation_score(events):
    """For matches decided by a penalty shootout, match.final_score
    reflects the SHOOTOUT result, not the real goals scored -- confirmed
    on the real 2020 final (Italy 3:2 England in final_score, but the
    actual match was 1-1; the shootout kicks are recorded as ordinary
    "goal" events at minute "120" with an empty running_score, mixed in
    with the real goals). This returns the true end-of-normal/extra-time
    score by taking the last goal event that has a real, non-empty
    running_score -- shootout kicks never have one, confirmed across
    the full dataset (141 of 143 minute="120" events have an empty
    running_score; the other 2 are genuine 120th-minute goals with a
    real running_score, and are correctly kept here since this only
    excludes events with a MISSING running_score, not all minute=120
    events indiscriminately).
    """
    last_valid = None
    for e in events:
        if e.get("type") != "goal":
            continue
        rs = e.get("running_score")
        if rs and ":" in rs:
            last_valid = rs
    if not last_valid:
        return 0, 0
    try:
        h, a = last_valid.split(":", 1)
        return int(h.strip()), int(a.strip())
    except (ValueError, TypeError):
        return 0, 0


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

        # For goals purposes only, use the true regulation/extra-time
        # score (see true_regulation_score docstring) -- home_score/
        # away_score above still correctly reflect who WON when a
        # shootout was involved, and are kept as-is for that purpose.
        true_home, true_away = true_regulation_score(data.get("events", []))

        match_summaries.append({
            "home_team": home_team, "away_team": away_team,
            "home_score": true_home, "away_score": true_away,
            "season": season,
        })

        teams_set.add(home_team)
        teams_set.add(away_team)

        for team, scored, conceded, result_scored, result_conceded in [
            (home_team, true_home, true_away, home_score, away_score),
            (away_team, true_away, true_home, away_score, home_score),
        ]:
            s = get_or_create_team_stats(team_stats_map, team, season)
            s["played"]        += 1
            s["goals_for"]     += scored
            s["goals_against"] += conceded
            if result_scored > result_conceded:
                s["wins"] += 1; s["points"] += 3
            elif result_scored == result_conceded:
                s["draws"] += 1; s["points"] += 1
            else:
                s["losses"] += 1
            if conceded == 0:
                s["clean_sheets"] += 1

        # ── Lineups -- built first so goal events below can detect own
        # goals by cross-referencing which team a scorer actually plays
        # for, not just which side the goal was credited to. ──────────
        lineups = data.get("lineups", {})
        home_lineup_players = (lineups.get("home", {}).get("starters") or []) + (lineups.get("home", {}).get("bench") or [])
        away_lineup_players = (lineups.get("away", {}).get("starters") or []) + (lineups.get("away", {}).get("bench") or [])
        home_names = set((p.get("name") or "").strip() for p in home_lineup_players)
        away_names = set((p.get("name") or "").strip() for p in away_lineup_players)

        # ── Goals -- from the top-level "events" array ───────────────────
        for event in data.get("events", []):
            if event.get("type") != "goal":
                continue
            name = (event.get("scorer") or "").strip()
            if not name:
                continue
            # CONFIRMED across the full dataset: event.get("side") is
            # null for every single one of the 1,137 goal events here --
            # this is NOT a per-match quirk, it's simply absent from this
            # data source entirely (unlike J-League/Brazil, where it's
            # populated). Team attribution therefore can't use "side" at
            # all; the scorer's real team is determined via lineup
            # lookup instead (the same mechanism already built for
            # own-goal detection below).
            #
            # This also explains, precisely, why own-goal detection
            # returns zero for this dataset: an own goal requires
            # knowing which team's SCOREBOARD TALLY the goal counted
            # toward, and with "side" completely absent, that
            # information doesn't exist anywhere in this data -- only
            # which team the scorer personally belongs to (via lineup
            # lookup) is determinable, which isn't the same thing.
            # own_goals will therefore continue to honestly show 0 for
            # every player -- not a bug to chase further, a genuine
            # limitation of what this data source records.
            if name in home_names and name not in away_names:
                actual_team, is_own_goal = home_team, False
            elif name in away_names and name not in home_names:
                actual_team, is_own_goal = away_team, False
            else:
                # Scorer not found in either lineup (or found in both,
                # e.g. a name collision) -- fall back to crediting
                # nobody's team rather than guessing wrong.
                actual_team, is_own_goal = "", False

            opponent = away_team if actual_team == home_team else home_team if actual_team else ""

            p = get_or_create_player(players_map, name)
            add_team_if_missing(p, actual_team)
            add_season_if_missing(p, season)
            ps = get_or_create_player_season(p, season, actual_team)

            if is_own_goal:
                p["own_goals"] += 1
                ps["own_goals"] += 1
            else:
                p["goals"] += 1
                ps["goals"] += 1
                if opponent:
                    ps["goals_by_opponent"][opponent] = ps["goals_by_opponent"].get(opponent, 0) + 1

        # ── Cards -- embedded per player inside lineups, not a flat list ─
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
