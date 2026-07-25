"""
Builds index.json and drivers.json from nascar_YYYY.json files.

Handles BOTH schemas that exist across this dataset's history:
  - Old (thethirdturn.com-sourced, 1949-2025): Fin, St, #, Driver,
    Sponsor, Make, Laps, Led, Status, Pts
  - New (nascar.com-sourced, 2026 onward): finishing_position,
    starting_position, car_number, driver_fullname, team_name,
    car_make, car_model, sponsor, laps_led, laps_completed,
    finishing_status, points_earned

Each result row is normalized into one common shape before being added
to a driver's history, so drivers.json looks consistent regardless of
which era/source a given season came from.

  index.json   -- [{ "year": 2026, "races": 25 }, ...]

  drivers.json -- [{ "name": "Ryan Blaney", "starts": 25, "wins": 3,
                      "races": [{"year":2026,"race_name":"...",
                                 "track_name":"...","finishing_position":1,
                                 "car":"...", ...}, ...] }, ...]

Run from the directory containing your nascar_YYYY.json files:

  python3 build_nascar_official_index.py --data-dir . --out-dir .
"""

import argparse
import glob
import json
import os
import re


def load_season_files(data_dir):
    # Matches nascar_YYYY.json specifically -- deliberately excludes
    # index.json/drivers.json themselves, since those don't have a
    # 4-digit-year filename.
    paths = sorted(glob.glob(os.path.join(data_dir, "nascar_*.json")))
    seasons = []
    for path in paths:
        m = re.search(r"nascar_(\d{4})\.json$", path)
        if not m:
            continue
        year = int(m.group(1))
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        seasons.append((year, data))
    if not seasons:
        raise SystemExit(f"No nascar_YYYY.json files found in {data_dir}")
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
    that's unique to the new (nascar.com) format."""
    is_new_schema = "driver_fullname" in result

    if is_new_schema:
        name = (result.get("driver_fullname") or "").strip()
        position = result.get("finishing_position")
        car = " ".join(filter(None, [result.get("car_make"), result.get("car_model")]))
        return {
            "name": name,
            "finishing_position": position,
            "starting_position": result.get("starting_position"),
            "car_number": result.get("car_number"),
            "team_name": result.get("team_name"),
            "car": car,
            "sponsor": result.get("sponsor"),
            "laps_led": result.get("laps_led"),
            "laps_completed": result.get("laps_completed"),
            "finishing_status": result.get("finishing_status"),
            "points_earned": result.get("points_earned"),
        }
    else:
        # Old thethirdturn.com schema. "Fin"/"St" are strings like "1",
        # "DNF" etc -- try to parse position as int for win detection,
        # but keep the raw string for display if it isn't purely numeric.
        name = (result.get("Driver") or "").strip()
        fin_raw = result.get("Fin")
        try:
            position = int(str(fin_raw).strip())
        except (TypeError, ValueError):
            position = fin_raw
        return {
            "name": name,
            "finishing_position": position,
            "starting_position": result.get("St"),
            "car_number": result.get("#"),
            "team_name": None,
            "car": result.get("Make"),
            "sponsor": result.get("Sponsor"),
            "laps_led": result.get("Led"),
            "laps_completed": result.get("Laps"),
            "finishing_status": result.get("Status"),
            "points_earned": result.get("Pts"),
        }


def build_drivers(seasons):
    drivers = {}  # name -> {starts, wins, races: []}

    for year, data in seasons:
        for race in data.get("races", []):
            race_id = race.get("race_id")
            race_name = race.get("race_name")
            track_name = race.get("track_name")
            for raw_result in race.get("results", []):
                r = normalize_result(raw_result)
                name = r["name"]
                if not name:
                    continue

                entry = drivers.setdefault(name, {"starts": 0, "wins": 0, "races": []})
                entry["starts"] += 1
                if r["finishing_position"] == 1:
                    entry["wins"] += 1

                entry["races"].append({
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

    out = []
    for name, entry in drivers.items():
        out.append({
            "name": name,
            "starts": entry["starts"],
            "wins": entry["wins"],
            "races": entry["races"],
        })
    out.sort(key=lambda d: -d["wins"])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=".",
                     help="Directory containing nascar_YYYY.json files")
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
