"""
Builds index.json and drivers.json from nascar_official_YYYY.json files
(the new nascar.com-sourced schema -- NOT compatible with the old
thethirdturn.com-based build_nascar_index.py, since the field names are
different: finishing_position vs Fin, driver_fullname vs Driver, etc).

  index.json   -- [{ "year": 2026, "races": 25 }, ...]

  drivers.json -- [{ "name": "Ryan Blaney", "starts": 25, "wins": 3,
                      "races": [{"year":2026,"race_name":"Quaker State 400",
                                 "track_name":"...", "finishing_position":1,
                                 "car_make":"Ford","car_model":"Mustang",
                                 "team_name":"Team Penske"}, ...] }, ...]

Run from the directory containing your nascar_official_YYYY.json files:

  python3 build_nascar_official_index.py --data-dir . --out-dir .
"""

import argparse
import glob
import json
import os
import re


def load_season_files(data_dir):
    paths = sorted(glob.glob(os.path.join(data_dir, "nascar_official_*.json")))
    if not paths:
        raise SystemExit(f"No nascar_official_*.json files found in {data_dir}")
    seasons = []
    for path in paths:
        m = re.search(r"nascar_official_(\d{4})\.json$", path)
        if not m:
            continue
        year = int(m.group(1))
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        seasons.append((year, data))
    seasons.sort(key=lambda x: x[0])
    return seasons


def build_index(seasons):
    return [
        {"year": year, "races": len(data.get("races", []))}
        for year, data in seasons
    ]


def build_drivers(seasons):
    drivers = {}  # name -> {starts, wins, races: []}

    for year, data in seasons:
        for race in data.get("races", []):
            race_name = race.get("race_name")
            track_name = race.get("track_name")
            race_id = race.get("race_id")
            for result in race.get("results", []):
                name = (result.get("driver_fullname") or "").strip()
                if not name:
                    continue

                entry = drivers.setdefault(name, {"starts": 0, "wins": 0, "races": []})
                entry["starts"] += 1
                position = result.get("finishing_position")
                if position == 1:
                    entry["wins"] += 1

                car = " ".join(filter(None, [result.get("car_make"), result.get("car_model")]))

                entry["races"].append({
                    "year": year,
                    "race_id": race_id,
                    "race_name": race_name,
                    "track_name": track_name,
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
                     help="Directory containing nascar_official_YYYY.json files")
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
