import requests
import json
from pathlib import Path
import time

print("F1 FULL HISTORY BUILDER STARTED")

BASE = "https://ergast.com/api/f1"
OUTPUT_DIR = Path("docs/data/f1")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

START_YEAR = 2009
END_YEAR = 2026  # change if needed


def get_json(url):
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("ERROR:", url, e)
        return None


for year in range(START_YEAR, END_YEAR + 1):

    print(f"\n===== BUILDING {year} =====")

    calendar = get_json(f"{BASE}/{year}.json")
    if not calendar:
        print("FAILED CALENDAR:", year)
        continue

    races = calendar["MRData"]["RaceTable"]["Races"]
    season_rows = []

    for race in races:

        round_num = race["round"]
        race_name = race["raceName"]
        date = race["date"]
        circuit = race["Circuit"]["circuitName"]
        location = race["Circuit"]["Location"]

        print(f"{year} Round {round_num} - {race_name}")

        results_json = get_json(f"{BASE}/{year}/{round_num}/results.json")

        if not results_json:
            continue

        results = results_json["MRData"]["RaceTable"]["Races"]
        if not results:
            continue

        race_results = results[0]["Results"]

        for r in race_results:

            driver = r["Driver"]
            constructor = r["Constructor"]

            row = {
                "season": year,
                "round": int(round_num),
                "race_name": race_name,
                "date": date,
                "circuit": circuit,
                "country": location["country"],

                "driver": f"{driver['givenName']} {driver['familyName']}",
                "driver_id": driver["driverId"],
                "constructor": constructor["name"],

                "grid": int(r.get("grid", 0)),
                "position": int(r.get("position", 0)),
                "points": float(r.get("points", 0)),
                "status": r.get("status"),
                "laps": int(r.get("laps", 0)),
                "time": r.get("Time", {}).get("time"),

                "fastest_lap_rank": r.get("FastestLap", {}).get("rank"),
                "fastest_lap_time": r.get("FastestLap", {}).get("Time", {}).get("time"),
            }

            season_rows.append(row)

        # avoid API hammering
        time.sleep(0.2)

    # SAVE SEASON
    out_file = OUTPUT_DIR / f"{year}.json"

    with open(out_file, "w") as f:
        json.dump(season_rows, f, indent=2)

    print(f"SAVED {year}: {len(season_rows)} rows")


print("\nDONE")
