"""
Builds index.json and drivers.json from supercars_YYYY.json files.

Handles BOTH schemas that exist across this dataset's history:
  - Old (thethirdturn.com-sourced): Fin, St, #, Driver, Sponsor, Make,
    Laps, Led, Status, Pts
  - New (supercars.com-sourced, 2026 onward): finishing_position,
    starting_position, car_number, driver_name, driver_url, team_name,
    race_time, laps, points

Each result row is normalized into one common shape before being added
to a driver's history, so drivers.json looks consistent regardless of
which era/source a given season came from.

  index.json   -- [{ "year": 2026, "races": 22 }, ...]

  drivers.json -- [{ "name": "Broc Feeney", "starts": 22, "wins": 4,
                      "races": [{"year":2026,"event_name":"...",
                                 "finishing_position":"1", ...}, ...] }, ...]

Run from the directory containing your supercars_YYYY.json files:

  python3 build_supercars_official_index.py --data-dir . --out-dir .
"""

import argparse
import glob
import json
import os
import re


def load_season_files(data_dir):
    # Matches supercars_YYYY.json specifically -- deliberately excludes
    # index.json/drivers.json themselves, since those don't have a
    # 4-digit-year filename.
    paths = sorted(glob.glob(os.path.join(data_dir, "supercars_*.json")))
    seasons = []
    for path in paths:
        m = re.search(r"supercars_(\d{4})\.json$", path)
        if not m:
            continue
        year = int(m.group(1))
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        seasons.append((year, data))
    if not seasons:
        raise SystemExit(f"No supercars_YYYY.json files found in {data_dir}")
    seasons.sort(key=lambda x: x[0])
    return seasons


def build_index(seasons):
    return [
        {"year": year, "races": len(data.get("races", []))}
        for year, data in seasons
    ]


def normalize_result(result):
    """Returns a common shape regardless of which era's schema this
    result row actually uses. Detects schema by checking for a field
    that's unique to the new (supercars.com) format."""
    is_new_schema = "driver_name" in result

    if is_new_schema:
        name = (result.get("driver_name") or "").strip()
        return {
            "name": name,
            "driver_url": result.get("driver_url"),
            "finishing_position": result.get("finishing_position"),
            "starting_position": result.get("starting_position"),
            "car_number": result.get("car_number"),
            "team_name": result.get("team_name"),
            "race_time": result.get("race_time"),
            "laps": result.get("laps"),
            "points": result.get("points"),
        }
    else:
        # Old thethirdturn.com schema.
        name = (result.get("Driver") or "").strip()
        return {
            "name": name,
            "driver_url": None,
            "finishing_position": result.get("Fin"),
            "starting_position": result.get("St"),
            "car_number": result.get("#"),
            "team_name": None,
            "race_time": None,
            "laps": result.get("Laps"),
            "points": result.get("Pts"),
        }


def build_drivers(seasons):
    drivers = {}  # name -> {starts, wins, races: [], driver_url}

    for year, data in seasons:
        for race in data.get("races", []):
            event_name = race.get("event_name") or race.get("track_text")
            race_label = race.get("race_label") or race.get("race_num")
            race_url = race.get("url")
            for raw_result in race.get("results", []):
                r = normalize_result(raw_result)
                name = r["name"]
                if not name:
                    continue

                entry = drivers.setdefault(name, {
                    "starts": 0, "wins": 0, "races": [],
                    "driver_url": r["driver_url"],
                })
                entry["starts"] += 1
                if str(r["finishing_position"]) == "1":
                    entry["wins"] += 1
                if not entry["driver_url"] and r["driver_url"]:
                    entry["driver_url"] = r["driver_url"]

                entry["races"].append({
                    "year": year,
                    "event_name": event_name,
                    "race_label": race_label,
                    "url": race_url,
                    "finishing_position": r["finishing_position"],
                    "starting_position": r["starting_position"],
                    "car_number": r["car_number"],
                    "team_name": r["team_name"],
                    "race_time": r["race_time"],
                    "laps": r["laps"],
                    "points": r["points"],
                })

    out = []
    for name, entry in drivers.items():
        out.append({
            "name": name,
            "driver_url": entry["driver_url"],
            "starts": entry["starts"],
            "wins": entry["wins"],
            "races": entry["races"],
        })
    out.sort(key=lambda d: -d["wins"])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=".",
                     help="Directory containing supercars_YYYY.json files")
    ap.add_argument("--out-dir", default=".",
                     help="Where to write index.json and drivers.json")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    seasons = load_season_files(args.data_dir)
    print(f"Loaded {len(seasons)} season(s): {seasons[0][0]}-{seasons[-1][0]}")

    index = build_index(seasons)
    index_path = os.path.join(args.out_dir, "index.json")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    print(f"Wrote {index_path} ({len(index)} season(s))")

    drivers = build_drivers(seasons)
    drivers_path = os.path.join(args.out_dir, "drivers.json")
    with open(drivers_path, "w", encoding="utf-8") as f:
        json.dump(drivers, f, indent=2, ensure_ascii=False)
    print(f"Wrote {drivers_path} ({len(drivers)} driver(s))")

    if drivers:
        top = drivers[0]
        print(f"\nMost wins: {top['name']} ({top['wins']} wins, {top['starts']} starts)")


if __name__ == "__main__":
    main()
