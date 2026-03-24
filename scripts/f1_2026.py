import requests
import json
from pathlib import Path

print("F1 2026 UPDATER STARTED")

BASE = "https://ergast.com/api/f1"
SEASON = 2026

OUTPUT = Path("docs/data/f1/2026.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)


def get_json(url):
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("ERROR:", url, e)
        return None


print("Loading calendar...")

calendar = get_json(f"{BASE}/{SEASON}.json")

if not calendar:
    print("FAILED TO LOAD CALENDAR")
    exit()

races = calendar["MRData"]["RaceTable"]["Races"]

all_rows = []

for race in races:

    round_num = race["round"]
    race_name = race["raceName"]
    date = race["date"]

    print(f"Checking Round {round_num} - {race_name}")

    results_json = get_json(f"{BASE}/{SEASON}/{round_num}/results.json")

    if not results_json:
        print("  → no data")
        continue

    results = results_json["MRData"]["RaceTable"]["Races"]

    # 🚨 KEY FIX → skip races with no results yet
    if not results:
        print("  → race not run yet")
        continue

    race_results = results[0]["Results"]

    for r in race_results:

        driver = r["Driver"]
        constructor = r["Constructor"]

        all_rows.append({
            "season": SEASON,
            "round": int(round_num),
            "race_name": race_name,
            "date": date,

            "driver": f"{driver['givenName']} {driver['familyName']}",
            "driver_id": driver["driverId"],
            "constructor": constructor["name"],

            "grid": int(r.get("grid", 0)),
            "position": int(r.get("position", 0)),
            "points": float(r.get("points", 0)),
            "status": r.get("status"),
        })


print("TOTAL ROWS:", len(all_rows))

# 🚨 FORCE DIFFERENCE EVERY RUN
data = {
    "last_updated": str(__import__("datetime").datetime.utcnow()),
    "rows": all_rows
}

with open(OUTPUT, "w") as f:
    json.dump(data, f, indent=2)

print("SAVED:", OUTPUT)
