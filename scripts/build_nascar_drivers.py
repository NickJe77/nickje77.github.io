#!/usr/bin/env python3
"""
build_nascar_drivers.py

Builds docs/data/nascar/drivers.json by aggregating every season file
in docs/data/nascar/nascar_{year}.json into per-driver career records.

Confirmed real structural facts used below -- two genuinely different
schemas exist across the season files, not one:

  OLD schema (thethirdturn.com-sourced, confirmed real on 2025 and
  earlier seasons):
    - Race-level info: race["info"]["title"] (e.g. "2025 Daytona 500
      - The Third Turn" -- confirmed real, needs the "- The Third
      Turn" suffix stripped) and race["info"]["venue_text"] (e.g.
      "Held on February 16, 2025 at Daytona International Speedway
      in Daytona Beach, FL" -- confirmed real, the actual track name
      sits between "at " and " in").
    - Per-driver result keys: Fin, St, #, Driver, Sponsor, Make,
      Laps, Led, Status, Pts. No team_name field exists at all in
      this schema.
    - This is the schema that was previously missing race_name/
      track_name entirely in drivers.json (both left null) -- the
      build script that produced the existing file simply never
      extracted them from this nested structure.

  NEW schema (nascar.com-sourced, confirmed real on 2026 onward):
    - Race-level info: race_name and track_name are direct fields.
    - Per-driver result keys: finishing_position, starting_position,
      car_number, driver_fullname, team_name, car_make, car_model,
      laps_led, laps_completed, finishing_status, points_earned.

Both schemas can appear under the exact same filename pattern
(nascar_{year}.json) -- confirmed real: nascar_2025.json is old-schema,
nascar_2026.json is new-schema. Detection is by which fields are
actually present on each race object, not by filename or year.

Usage:
    python3 build_nascar_drivers.py --data-dir ./docs/data/nascar --out ./docs/data/nascar/drivers.json
"""

import argparse
import json
import os
import re
import urllib.request
from collections import defaultdict


def extract_old_schema_race_name(info):
    """'2025 Daytona 500 - The Third Turn' -> '2025 Daytona 500'
    (confirmed real title format)."""
    title = (info or {}).get("title") or ""
    return re.sub(r"\s*-\s*The Third Turn\s*$", "", title).strip() or None


def extract_old_schema_track_name(info):
    """'Held on February 16, 2025 at Daytona International Speedway
    in Daytona Beach, FL' -> 'Daytona International Speedway'
    (confirmed real venue_text format)."""
    venue_text = (info or {}).get("venue_text") or ""
    m = re.search(r"at (.+?) in", venue_text)
    return m.group(1).strip() if m else None


def to_int(v):
    try:
        return int(str(v).strip())
    except (ValueError, TypeError):
        return None


def normalize_race(race):
    """Returns (race_name, track_name, race_id, list_of_normalized_results)
    regardless of which schema this race object actually uses."""
    if "race_name" in race:
        # New (nascar.com) schema -- fields are direct.
        race_name = race.get("race_name")
        track_name = race.get("track_name")
        race_id = race.get("race_id")
        results = []
        for r in race.get("results", []):
            results.append({
                "driver_name": r.get("driver_fullname"),
                "finishing_position": to_int(r.get("finishing_position")),
                "starting_position": r.get("starting_position"),
                "car_number": r.get("car_number"),
                "team_name": r.get("team_name"),
                "car": " ".join(filter(None, [r.get("car_make"), r.get("car_model")])) or None,
                "sponsor": r.get("sponsor"),
                "laps_led": r.get("laps_led"),
                "laps_completed": r.get("laps_completed"),
                "finishing_status": r.get("finishing_status"),
                "points_earned": r.get("points_earned"),
            })
        return race_name, track_name, race_id, results

    else:
        # Old (thethirdturn.com) schema -- race name/track are nested
        # in "info" and were previously never extracted at all.
        info = race.get("info", {})
        race_name = extract_old_schema_race_name(info)
        track_name = extract_old_schema_track_name(info)
        race_id = None  # confirmed: no equivalent numeric ID exists in this schema
        results = []
        for r in race.get("results", []):
            results.append({
                "driver_name": r.get("Driver"),
                "finishing_position": to_int(r.get("Fin")),
                "starting_position": r.get("St"),
                "car_number": r.get("#"),
                "team_name": None,  # confirmed: no separate team_name field in this schema
                "car": r.get("Make"),
                "sponsor": r.get("Sponsor"),
                "laps_led": r.get("Led"),
                "laps_completed": r.get("Laps"),
                "finishing_status": r.get("Status"),
                "points_earned": r.get("Pts"),
            })
        return race_name, track_name, race_id, results


def fetch_url(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def list_github_season_files(repo, path):
    """Lists every nascar_{year}.json file directly from the live repo
    via the GitHub API, so this doesn't require a local clone."""
    api_url = f"https://api.github.com/repos/{repo}/contents/{path}"
    data = json.loads(fetch_url(api_url))
    if not isinstance(data, list):
        raise RuntimeError(f"GitHub API error: {data.get('message', data)}")
    return [f["download_url"] for f in data
            if re.match(r"^nascar_\d{4}\.json$", f["name"])]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir",
                     help="Directory containing nascar_{year}.json season files (local mode)")
    ap.add_argument("--github", metavar="OWNER/REPO",
                     help="Fetch season files directly from a live GitHub repo instead "
                          "of a local directory, e.g. --github NickJe77/nickje77.github.io")
    ap.add_argument("--github-path", default="docs/data/nascar",
                     help="Path within the repo where the season files live "
                          "(only used with --github)")
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
                               if re.match(r"^nascar_\d{4}\.json$", f))
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
            race_name, track_name, race_id, results = normalize_race(race)

            for r in results:
                driver_name = r.get("driver_name")
                if not driver_name:
                    continue

                drivers[driver_name].append({
                    "year": year,
                    "race_id": race_id,
                    "race_name": race_name,
                    "track_name": track_name,
                    "finishing_position": r["finishing_position"],
                    "starting_position": r["starting_position"],
                    "car_number": r["car_number"],
                    "team_name": r["team_name"],
                    "car": r["car"],
                    "sponsor": r["sponsor"],
                    "laps_led": r["laps_led"],
                    "laps_completed": r["laps_completed"],
                    "finishing_status": r["finishing_status"],
                    "points_earned": r["points_earned"],
                })

        print(f"  {fname}: {len(races)} race(s) processed")

    output = [{"name": name, "races": races} for name, races in drivers.items()]
    output.sort(key=lambda d: d["name"])

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nWrote {len(output)} driver(s) -> {args.out}")


if __name__ == "__main__":
    main()
