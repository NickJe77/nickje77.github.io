#!/usr/bin/env python3
"""
nfl_build_boxscores.py

Populates docs/data/nfl/boxscores/{season}/{game_id}.json using nflverse's
"stats_player" release, which updates nightly during the season (and is
plain GitHub-hosted CSV, so it isn't blocked from GitHub Actions the way
pro-football-reference.com and site.api.espn.com are).

Source: https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_{season}.csv

Run this AFTER nfl_scrape_season.py for the same season (it doesn't need
the season file, but keeping the same order matches the existing workflow
step layout).

Usage:
    python3 scripts/nfl_build_boxscores.py 2026
"""

import csv
import io
import json
import os
import sys

import requests

STATS_URL_TMPL = ("https://github.com/nflverse/nflverse-data/releases/download/"
                   "stats_player/stats_player_week_{season}.csv")

OUT_ROOT = "docs/data/nfl"
BOXSCORE_DIR = f"{OUT_ROOT}/boxscores"


def to_num(val, cast=int):
    try:
        return cast(float(val))
    except (TypeError, ValueError):
        return 0


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/nfl_build_boxscores.py <season>")
        sys.exit(1)

    season = int(sys.argv[1])
    url = STATS_URL_TMPL.format(season=season)

    print(f"Downloading {url} ...")
    res = requests.get(url, timeout=60)
    if res.status_code == 404:
        print("No stats_player file for this season yet — nothing to do.")
        return
    res.raise_for_status()
    print(f"  got {len(res.content)} bytes")

    reader = csv.DictReader(io.StringIO(res.text))

    # group rows by game_id
    by_game = {}
    for row in reader:
        gid = row.get("game_id")
        if not gid:
            continue
        by_game.setdefault(gid, []).append(row)

    box_dir = f"{BOXSCORE_DIR}/{season}"
    os.makedirs(box_dir, exist_ok=True)

    written = 0
    for gid, rows in by_game.items():
        out = {
            "game_id": gid,
            "passing": [], "rushing": [], "receiving": [],
            "defense": [], "kicking": [], "returns": [], "scoring": [],
        }

        for row in rows:
            name = row.get("player_display_name") or row.get("player_name") or ""
            team = row.get("team", "")

            attempts = to_num(row.get("attempts"))
            if attempts > 0:
                out["passing"].append({"player": name, "stats": {
                    "team": team,
                    "pass_cmp": to_num(row.get("completions")),
                    "pass_att": attempts,
                    "pass_yds": to_num(row.get("passing_yards")),
                    "pass_td": to_num(row.get("passing_tds")),
                    "pass_int": to_num(row.get("passing_interceptions")),
                }})

            carries = to_num(row.get("carries"))
            if carries > 0:
                out["rushing"].append({"player": name, "stats": {
                    "team": team,
                    "rush_att": carries,
                    "rush_yds": to_num(row.get("rushing_yards")),
                    "rush_td": to_num(row.get("rushing_tds")),
                }})

            receptions = to_num(row.get("receptions"))
            targets = to_num(row.get("targets"))
            if targets > 0:
                out["receiving"].append({"player": name, "stats": {
                    "team": team,
                    "rec": receptions,
                    "targets": targets,
                    "rec_yds": to_num(row.get("receiving_yards")),
                    "rec_td": to_num(row.get("receiving_tds")),
                }})

            def_tackles = to_num(row.get("def_tackles_solo")) + to_num(row.get("def_tackle_assists"))
            def_sacks = to_num(row.get("def_sacks"), float)
            def_ints = to_num(row.get("def_interceptions"))
            if def_tackles or def_sacks or def_ints:
                out["defense"].append({"player": name, "stats": {
                    "team": team,
                    "tackles": def_tackles,
                    "sacks": def_sacks,
                    "int": def_ints,
                    "pd": to_num(row.get("def_pass_defended")),
                }})

            fg_att = to_num(row.get("fg_att"))
            pat_att = to_num(row.get("pat_att"))
            if fg_att or pat_att:
                out["kicking"].append({"player": name, "stats": {
                    "team": team,
                    "fg_made": to_num(row.get("fg_made")),
                    "fg_att": fg_att,
                    "pat_made": to_num(row.get("pat_made")),
                    "pat_att": pat_att,
                }})

            kr = to_num(row.get("kickoff_returns"))
            pr = to_num(row.get("punt_returns"))
            if kr or pr:
                out["returns"].append({"player": name, "stats": {
                    "team": team,
                    "kr": kr,
                    "kr_yds": to_num(row.get("kickoff_return_yards")),
                    "pr": pr,
                    "pr_yds": to_num(row.get("punt_return_yards")),
                }})

        with open(f"{box_dir}/{gid}.json", "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, ensure_ascii=False)
        written += 1

    print(f"Wrote {written} boxscore files to {box_dir}/")


if __name__ == "__main__":
    main()
