"""
Builds index.json and drivers.json from supercars_official_YYYY.json
files (the new supercars.com-sourced schema).

  index.json   -- [{ "year": 2026, "races": 22 }, ...]

  drivers.json -- [{ "name": "Broc Feeney", "starts": 22, "wins": 4,
                      "races": [{"year":2026,"event_name":"...",
                                 "race_label":"R2","finishing_position":"1",
                                 "starting_position":"3","car_number":"88",
                                 "team_name":"Red Bull Ampol Racing",
                                 "race_time":"40:14.592","laps":"26",
                                 "points":"+60"}, ...] }, ...]

Run from the directory containing your supercars_official_YYYY.json files:

  python3 build_supercars_official_index.py --data-dir . --out-dir .
"""

import argparse
import glob
import json
import os
import re


def load_season_files(data_dir):
    paths = sorted(glob.glob(os.path.join(data_dir, "supercars_official_*.json")))
    if not paths:
        raise SystemExit(f"No supercars_official_*.json files found in {data_dir}")
    seasons = []
    for path in paths:
        m = re.search(r"supercars_official_(\d{4})\.json$", path)
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
            event_name = race.get("event_name")
            race_label = race.get("race_label")
            race_url = race.get("url")
            for result in race.get("results", []):
                name = (result.get("driver_name") or "").strip()
                if not name:
                    continue

                entry = drivers.setdefault(name, {
                    "starts": 0, "wins": 0, "races": [],
                    "driver_url": result.get("driver_url"),
                })
                entry["starts"] += 1
                position = result.get("finishing_position")
                if position == "1":
                    entry["wins"] += 1

                entry["races"].append({
                    "year": year,
                    "event_name": event_name,
                    "race_label": race_label,
                    "url": race_url,
                    "finishing_position": position,
                    "starting_position": result.get("starting_position"),
                    "car_number": result.get("car_number"),
                    "team_name": result.get("team_name"),
                    "race_time": result.get("race_time"),
                    "laps": result.get("laps"),
                    "points": result.get("points"),
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
                     help="Directory containing supercars_official_YYYY.json files")
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
