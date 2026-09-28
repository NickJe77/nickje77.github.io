#!/usr/bin/env python3
"""
build_supercars_drivers.py

Builds docs/data/supercars/drivers.json by aggregating every season
file in docs/data/supercars/supercars_{year}.json into per-driver
career records.

Confirmed real schema (via supercars_2026.json) -- only one format
exists here, unlike NASCAR's old/new split:
  - Race-level: url, event_name, race_label, results
  - Per-driver result: finishing_position (a string, "-" for DNF --
    confirmed real), starting_position, car_number, driver_name,
    driver_url, team_name, race_time, laps, points

Each race is identified by its own url (confirmed real: this is the
same identifier supercars-season.html and supercars-race.html already
use to link between pages -- there's no separate numeric race_id in
this data at all, so url is the only stable identifier).

Usage:
    python3 build_supercars_drivers.py --data-dir ./docs/data/supercars --out ./docs/data/supercars/drivers.json
    python3 build_supercars_drivers.py --github NickJe77/nickje77.github.io --out ./drivers.json
"""

import argparse
import json
import os
import re
import urllib.request
from collections import defaultdict


def extract_old_schema_race_name(info):
    """'ATCC:1997-01 - The Third Turn' -> 'ATCC:1997-01' (confirmed
    real title format, same pattern as NASCAR's old schema)."""
    title = (info or {}).get("title") or ""
    return re.sub(r"\s*-\s*The Third Turn\s*$", "", title).strip() or None


def extract_old_schema_track_name(info):
    """'Held on March 15, 1997 at Calder Park Raceway in Keilor, VIC,
    Australia' -> 'Calder Park Raceway' (confirmed real venue_text
    format)."""
    venue_text = (info or {}).get("venue_text") or ""
    m = re.search(r"at (.+?) in", venue_text)
    return m.group(1).strip() if m else None


def normalize_race_and_results(race):
    """Returns (event_name, race_label, results) regardless of which
    real schema this race object actually uses -- confirmed both
    schemas exist across real season files under the identical
    filename pattern (supercars_{year}.json)."""
    if "results" in race and race["results"] and "driver_name" in race["results"][0]:
        # New (supercars.com) schema -- fields are direct.
        return race.get("event_name"), race.get("race_label"), [
            {
                "driver_name": r.get("driver_name"),
                "finishing_position": r.get("finishing_position"),
                "starting_position": r.get("starting_position"),
                "car_number": r.get("car_number"),
                "team_name": r.get("team_name"),
                "laps": r.get("laps"),
                "points": r.get("points"),
            }
            for r in race["results"]
        ]
    else:
        # Old (thethirdturn.com) schema -- race name/track nested in
        # "info", no separate team_name field at all (confirmed real).
        info = race.get("info", {})
        event_name = extract_old_schema_race_name(info)
        race_label = f"Round {race.get('race_num')}" if race.get("race_num") else None
        results = [
            {
                "driver_name": r.get("Driver"),
                "finishing_position": r.get("Fin"),
                "starting_position": r.get("St"),
                "car_number": r.get("#"),
                "team_name": None,  # confirmed: no equivalent field in this schema
                "laps": r.get("Laps"),
                "points": r.get("Pts"),
            }
            for r in race.get("results", [])
        ]
        return event_name, race_label, results


def fetch_url(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def list_github_season_files(repo, path):
    api_url = f"https://api.github.com/repos/{repo}/contents/{path}"
    data = json.loads(fetch_url(api_url))
    if not isinstance(data, list):
        raise RuntimeError(f"GitHub API error: {data.get('message', data)}")
    return [f["download_url"] for f in data
            if re.match(r"^supercars_\d{4}\.json$", f["name"])]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir",
                     help="Directory containing supercars_{year}.json season files (local mode)")
    ap.add_argument("--github", metavar="OWNER/REPO",
                     help="Fetch season files directly from a live GitHub repo instead "
                          "of a local directory")
    ap.add_argument("--github-path", default="docs/data/supercars")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    if not args.data_dir and not args.github:
        ap.error("either --data-dir or --github is required")

    drivers = defaultdict(list)

    if args.github:
        print(f"Listing season files from https://github.com/{args.github}/{args.github_path}...")
        urls = list_github_season_files(args.github, args.github_path)
        print(f"Found {len(urls)} season file(s).")
        season_sources = [(url.rsplit("/", 1)[-1], fetch_url(url)) for url in urls]
    else:
        season_files = sorted(f for f in os.listdir(args.data_dir)
                               if re.match(r"^supercars_\d{4}\.json$", f))
        print(f"Found {len(season_files)} season file(s).")
        season_sources = []
        for fname in season_files:
            with open(os.path.join(args.data_dir, fname), encoding="utf-8") as f:
                season_sources.append((fname, f.read()))

    for fname, raw_text in season_sources:
        season_data = json.loads(raw_text)
        year = season_data.get("year")
        races = season_data.get("races", [])

        for race in races:
            event_name, race_label, results = normalize_race_and_results(race)

            for r in results:
                driver_name = r.get("driver_name")
                if not driver_name:
                    continue

                drivers[driver_name].append({
                    "year": year,
                    "url": race.get("url"),
                    "event_name": event_name,
                    "race_label": race_label,
                    "finishing_position": r.get("finishing_position"),
                    "starting_position": r.get("starting_position"),
                    "car_number": r.get("car_number"),
                    "team_name": r.get("team_name"),
                    "laps": r.get("laps"),
                    "points": r.get("points"),
                })

        print(f"  {fname}: {len(races)} race(s) processed")

    output = []
    for name, races in drivers.items():
        # finishing_position is a string here ("1", "2", ..., "-" for
        # DNF -- confirmed real), so compare as a string, not int.
        wins = sum(1 for r in races if str(r.get("finishing_position")) == "1")
        output.append({
            "name": name,
            "starts": len(races),
            "wins": wins,
            "races": races,
        })
    output.sort(key=lambda d: d["name"])

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nWrote {len(output)} driver(s) -> {args.out}")


if __name__ == "__main__":
    main()
