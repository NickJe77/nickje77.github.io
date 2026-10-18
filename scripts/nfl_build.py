#!/usr/bin/env python3
"""
Build NFL season files with players + fantasy points (runs in GitHub Actions)
============================================================================
Writes season files in the site's existing NFL layout:

    {"season", "source", "updated", "games": [
        {"game_id", "date", "week", "team1", "team2", "score1", "score2", "venue",
         "players": [ ...each player's stats and fantasy points... ] }, ... ]}

straight from nflverse. team1 = away team, team2 = home team.
Each player has fantasy_points_std, fantasy_points_half (half-PPR), fantasy_points_ppr.

Run by .github/workflows/nfl-fantasy.yml. Can also be run by hand:
    python scripts/nfl_build.py              -> current season only
    python scripts/nfl_build.py 1999 2026    -> a range of seasons

Output folder: env NFL_OUT (default docs/data/nfl/seasons)
"""

import os
import sys
import json
import math
import datetime
from pathlib import Path

today = datetime.date.today()
CURRENT_SEASON = today.year if today.month >= 3 else today.year - 1   # NFL season spans the new year

args = [a for a in sys.argv[1:] if a.strip()]
START_YEAR = int(args[0]) if args else CURRENT_SEASON
END_YEAR   = int(args[1]) if len(args) > 1 else START_YEAR
OUT_DIR    = Path(os.environ.get("NFL_OUT", "docs/data/nfl/seasons"))
OUT_DIR.mkdir(parents=True, exist_ok=True)
SOURCE     = "https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv"

# nflverse abbreviation -> full name (including old franchise locations)
TEAMS = {
    "ARI": "Arizona Cardinals", "ATL": "Atlanta Falcons", "BAL": "Baltimore Ravens",
    "BUF": "Buffalo Bills", "CAR": "Carolina Panthers", "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals", "CLE": "Cleveland Browns", "DAL": "Dallas Cowboys",
    "DEN": "Denver Broncos", "DET": "Detroit Lions", "GB": "Green Bay Packers",
    "HOU": "Houston Texans", "IND": "Indianapolis Colts", "JAX": "Jacksonville Jaguars",
    "KC": "Kansas City Chiefs", "LV": "Las Vegas Raiders", "LAC": "Los Angeles Chargers",
    "LA": "Los Angeles Rams", "LAR": "Los Angeles Rams", "MIA": "Miami Dolphins",
    "MIN": "Minnesota Vikings", "NE": "New England Patriots", "NO": "New Orleans Saints",
    "NYG": "New York Giants", "NYJ": "New York Jets", "PHI": "Philadelphia Eagles",
    "PIT": "Pittsburgh Steelers", "SF": "San Francisco 49ers", "SEA": "Seattle Seahawks",
    "TB": "Tampa Bay Buccaneers", "TEN": "Tennessee Titans", "WAS": "Washington Commanders",
    "OAK": "Oakland Raiders", "SD": "San Diego Chargers", "STL": "St. Louis Rams",
}
def team_name(abbr, season):
    if abbr == "WAS":
        return ("Washington Redskins" if season <= 2019 else
                "Washington Football Team" if season <= 2021 else "Washington Commanders")
    return TEAMS.get(abbr, abbr)

PFIELDS = {
    "player_id":       ["player_id", "gsis_id"],
    "player":          ["player_display_name", "player_name"],
    "position":        ["position"],
    "team":            ["team", "recent_team"],
    "opponent":        ["opponent_team", "opponent"],
    "week":            ["week"],
    "game_id":         ["game_id"],
    "completions":     ["completions"],
    "attempts":        ["attempts", "passing_attempts"],
    "passing_yards":   ["passing_yards"],
    "passing_tds":     ["passing_tds"],
    "interceptions":   ["passing_interceptions", "interceptions"],
    "sacks":           ["sacks_suffered", "sacks"],
    "carries":         ["carries", "rushing_attempts"],
    "rushing_yards":   ["rushing_yards"],
    "rushing_tds":     ["rushing_tds"],
    "targets":         ["targets"],
    "receptions":      ["receptions"],
    "receiving_yards": ["receiving_yards"],
    "receiving_tds":   ["receiving_tds"],
    "fumbles_lost":    ["fumbles_lost"],
    "two_pt":          ["two_pt_conversions"],
    "fantasy_points_std": ["fantasy_points"],
    "fantasy_points_ppr": ["fantasy_points_ppr"],
}
PLAYER_OUT = ["player", "player_id", "position", "team",
              "fantasy_points_std", "fantasy_points_half", "fantasy_points_ppr",
              "completions", "attempts", "passing_yards", "passing_tds", "interceptions", "sacks",
              "carries", "rushing_yards", "rushing_tds",
              "targets", "receptions", "receiving_yards", "receiving_tds", "fumbles_lost", "two_pt"]


def clean(v):
    if v is None:
        return None
    if isinstance(v, float):
        if math.isnan(v):
            return None
        return int(v) if v.is_integer() else round(v, 2)
    if hasattr(v, "isoformat"):
        return v.isoformat()[:10]
    return v

def num(v):
    return v if isinstance(v, (int, float)) else 0

def records(df):
    return df.to_dicts() if hasattr(df, "to_dicts") else df.to_dict("records")

def load(year):
    import nflreadpy as nfl
    return (records(nfl.load_schedules(seasons=[year])),
            records(nfl.load_player_stats(seasons=[year], summary_level="week")))

def pick(r, names):
    for n in names:
        if n in r and r[n] is not None:
            return clean(r[n])
    return None

def shape_player(r):
    p = {k: pick(r, names) for k, names in PFIELDS.items()}
    if p["fumbles_lost"] is None:
        p["fumbles_lost"] = sum(num(clean(r.get(k))) for k in
                                ("rushing_fumbles_lost", "receiving_fumbles_lost", "sack_fumbles_lost"))
    if p["two_pt"] is None:
        p["two_pt"] = sum(num(clean(r.get(k))) for k in
                          ("passing_2pt_conversions", "rushing_2pt_conversions", "receiving_2pt_conversions"))
    if p["fantasy_points_std"] is None:
        p["fantasy_points_std"] = round(
            num(p["passing_yards"]) / 25 + 4 * num(p["passing_tds"]) - 2 * num(p["interceptions"])
            + num(p["rushing_yards"]) / 10 + 6 * num(p["rushing_tds"])
            + num(p["receiving_yards"]) / 10 + 6 * num(p["receiving_tds"])
            - 2 * num(p["fumbles_lost"]) + 2 * num(p["two_pt"]), 2)
    rec = num(p["receptions"])
    if p["fantasy_points_ppr"] is None:
        p["fantasy_points_ppr"] = round(p["fantasy_points_std"] + rec, 2)
    p["fantasy_points_half"] = round(p["fantasy_points_std"] + 0.5 * rec, 2)
    return p

def has_stats(p):
    return any(num(p.get(k)) != 0 for k in PLAYER_OUT[4:])


def build(year):
    sched, stats = load(year)
    sched = [s for s in sched if int(s.get("season") or year) == year]
    if not sched:
        print(f"  [{year}] no schedule found")
        return

    players = [p for p in (shape_player(r) for r in stats) if has_stats(p)]
    by_id, by_teams = {}, {}
    for p in players:
        if p.get("game_id"):
            by_id.setdefault(p["game_id"], []).append(p)
        if p.get("week") is not None and p.get("team") and p.get("opponent"):
            by_teams.setdefault((int(p["week"]), frozenset((p["team"], p["opponent"]))), []).append(p)

    games, played, with_players, n_players = [], 0, 0, 0
    sched.sort(key=lambda s: (int(s.get("week") or 0), str(clean(s.get("gameday")) or ""), str(s.get("game_id"))))
    for s in sched:
        away, home, gid = s.get("away_team"), s.get("home_team"), s.get("game_id")
        g = {
            "game_id": gid,
            "date":    clean(s.get("gameday")),
            "week":    str(clean(s.get("week"))),
            "team1":   team_name(away, year),
            "team2":   team_name(home, year),
            "score1":  clean(s.get("away_score")),
            "score2":  clean(s.get("home_score")),
            "venue":   s.get("stadium"),
        }
        if g["score1"] is not None and g["score2"] is not None:
            played += 1
            plist = by_id.get(gid) or by_teams.get((int(s.get("week") or 0), frozenset((away, home)))) or []
            if plist:
                with_players += 1
                n_players += len(plist)
                g["players"] = [dict({k: p.get(k) for k in PLAYER_OUT}, home=(p["team"] == home))
                                for p in sorted(plist, key=lambda p: -num(p.get("fantasy_points_ppr")))]
        games.append(g)

    data = {"season": year, "source": SOURCE,
            "updated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "games": games}
    out = OUT_DIR / f"{year}.json"
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  [{year}] {len(games)} games ({played} played, {with_players} with players, "
          f"{n_players} player-games) → {out}")


def main():
    print(f"NFL season files with fantasy points — {START_YEAR} to {END_YEAR} → {OUT_DIR}")
    failed = []
    for y in range(START_YEAR, END_YEAR + 1):
        try:
            build(y)
        except Exception as e:
            print(f"  [{y}] failed: {e}")
            failed.append(y)
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
