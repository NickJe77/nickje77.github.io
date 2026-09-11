#!/usr/bin/env python3
"""
rebuild_tennis_seasons_current.py

tennis-data.co.uk started blocking automated requests (403 Forbidden) from
GitHub Actions, the same way pro-football-reference.com did for the NFL
scraper. Rather than fight another bot-wall, this version pulls from a
GitHub-hosted, continuously-updated mirror of Jeff Sackmann's original
tennis_atp/tennis_wta match data (the source this site's historical files
like 1985.json were already built from):

    https://github.com/Aneeshers/tennis-sackmann-archive

Since it's plain files on GitHub, there's no bot-wall to hit. It also
means real full player names and real match stats (aces, break points,
etc.) are available again — no more name-abbreviation workarounds and no
more zeroed-out stat fields.

Output schema for docs/data/tennis/seasons/{year}.json is UNCHANGED:
    { "matches": [ { "match_id", "date", "tournament", "surface", "round",
                      "player1", "player2", "winner", "loser", "score",
                      "gender", "best_of", "draw_size", "minutes",
                      "tourney_level", "tourney_id",
                      "w_ace", "w_df", "w_svpt", "w_1stIn", "w_1stWon",
                      "w_2ndWon", "w_SvGms", "w_bpSaved", "w_bpFaced",
                      "l_ace", "l_df", "l_svpt", "l_1stIn", "l_1stWon",
                      "l_2ndWon", "l_SvGms", "l_bpSaved", "l_bpFaced" }, ... ] }

Usage:
    python3 scripts/rebuild_tennis_seasons_current.py
"""

import csv
import io
import json
import os
from datetime import date

import requests

BASE = "docs/data/tennis/seasons"

CURRENT_YEAR = date.today().year
PREV_YEAR = CURRENT_YEAR - 1

RAW_BASE = "https://raw.githubusercontent.com/Aneeshers/tennis-sackmann-archive/main"


def make_urls(year):
    return {
        "M": f"{RAW_BASE}/atp/atp_matches_{year}.csv",
        "F": f"{RAW_BASE}/wta/wta_matches_{year}.csv",
    }


def to_int(val, default=0):
    try:
        return int(float(val))
    except (TypeError, ValueError):
        return default


def fetch(url, gender):
    r = requests.get(url, timeout=60)
    if r.status_code == 404:
        print(f"  Not found (404): {url}")
        return []
    r.raise_for_status()

    reader = csv.DictReader(io.StringIO(r.text))
    gender_char = "m" if gender == "M" else "f"

    matches = []
    for row in reader:
        raw_date = (row.get("tourney_date") or "").strip()
        if len(raw_date) != 8:
            continue
        date_str = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:8]}"

        winner = (row.get("winner_name") or "").strip()
        loser = (row.get("loser_name") or "").strip()
        tournament = (row.get("tourney_name") or "").strip()
        round_ = (row.get("round") or "").strip()

        if not winner or not loser:
            continue

        tournament_slug = tournament.replace(" ", "-").lower()
        winner_slug = winner.replace(" ", "-").lower()
        loser_slug = loser.replace(" ", "-").lower()
        round_slug = round_.lower()
        year_str = date_str[:4]

        match_id = (f"{year_str}_{gender_char}_{date_str}_{tournament_slug}_"
                    f"{round_slug}_{winner_slug}_{loser_slug}")

        matches.append({
            "match_id": match_id,
            "date": date_str,
            "tournament": tournament,
            "surface": (row.get("surface") or "").strip(),
            "round": round_,
            "player1": winner,
            "player2": loser,
            "winner": winner,
            "loser": loser,
            "score": (row.get("score") or "").strip(),
            "gender": gender,
            "best_of": to_int(row.get("best_of"), 3),
            "draw_size": to_int(row.get("draw_size")),
            "minutes": to_int(row.get("minutes")),
            "tourney_level": (row.get("tourney_level") or "").strip(),
            "tourney_id": (row.get("tourney_id") or "").strip(),
            "w_ace": to_int(row.get("w_ace")),
            "w_df": to_int(row.get("w_df")),
            "w_svpt": to_int(row.get("w_svpt")),
            "w_1stIn": to_int(row.get("w_1stIn")),
            "w_1stWon": to_int(row.get("w_1stWon")),
            "w_2ndWon": to_int(row.get("w_2ndWon")),
            "w_SvGms": to_int(row.get("w_SvGms")),
            "w_bpSaved": to_int(row.get("w_bpSaved")),
            "w_bpFaced": to_int(row.get("w_bpFaced")),
            "l_ace": to_int(row.get("l_ace")),
            "l_df": to_int(row.get("l_df")),
            "l_svpt": to_int(row.get("l_svpt")),
            "l_1stIn": to_int(row.get("l_1stIn")),
            "l_1stWon": to_int(row.get("l_1stWon")),
            "l_2ndWon": to_int(row.get("l_2ndWon")),
            "l_SvGms": to_int(row.get("l_SvGms")),
            "l_bpSaved": to_int(row.get("l_bpSaved")),
            "l_bpFaced": to_int(row.get("l_bpFaced")),
        })

    return matches


def filter_past(matches, year):
    today = date.today().isoformat()
    if str(year) != str(date.today().year):
        return matches
    return [m for m in matches if m["date"] <= today]


def save(year, matches):
    os.makedirs(BASE, exist_ok=True)
    path = f"{BASE}/{year}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"matches": matches}, f, indent=2, ensure_ascii=False)
    print(f"  Saved {path} ({len(matches)} matches)")


def build_season(year):
    print(f"\nBuilding {year}...")
    urls = make_urls(year)
    all_matches = []

    for gender, url in urls.items():
        label = "ATP" if gender == "M" else "WTA"
        print(f"  Fetching {label} {year}...")
        matches = fetch(url, gender)
        print(f"    -> {len(matches)} matches")
        all_matches.extend(matches)

    if not all_matches:
        print(f"  No data found for {year}, skipping.")
        return

    filtered = filter_past(all_matches, year)
    removed = len(all_matches) - len(filtered)
    if removed:
        print(f"  ({removed} future matches removed)")

    save(year, filtered)


def main():
    build_season(CURRENT_YEAR)
    build_season(PREV_YEAR)
    print("\nDONE — files written to", BASE)


if __name__ == "__main__":
    main()
