import requests
import json
from pathlib import Path
from datetime import datetime

print("F1 2026 FINAL BUILDER (CLEAN)")

BASE = "https://api.jolpi.ca/ergast/f1"
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


# -----------------------------
# GET RACE CALENDAR
# -----------------------------
calendar = get_json(f"{BASE}/{SEASON}.json")

if not calendar:
    print("FAILED TO LOAD CALENDAR")
    exit()

races = calendar["MRData"]["RaceTable"]["Races"]

season_data = []

for race in races:

    round_num = int(race["round"])
    race_name = race["raceName"]

    print(f"Round {round_num} - {race_name}")

    results_json = get_json(f"{BASE}/{SEASON}/{round_num}/results.json")

    if not results_json:
        continue

    race_block = results_json["MRData"]["RaceTable"]["Races"]

    if not race_block:
        continue

    results = []

    fastest_driver = None
    fastest_time = None

    for r in race_block[0]["Results"]:

        driver = r["Driver"]
        constructor = r["Constructor"]

        # -----------------------------
        # DRIVER NAME (FIXED)
        # -----------------------------
        name = f"{driver['givenName']} {driver['familyName']}"

        # fix Antonelli
        if name.startswith("Andrea Kimi Antonelli"):
            name = "Kimi Antonelli"

        # -----------------------------
        # FASTEST LAP
        # -----------------------------
        fl = r.get("FastestLap")
        if fl and fl.get("rank") == "1":
            fastest_driver = name
            fastest_time = fl["Time"]["time"]

        results.append({
            "position": int(r.get("position", 0)),
            "driver": name,
            "team": constructor["name"],
            "grid": int(r.get("grid", 0)),
            "time": r.get("Time", {}).get("time"),
            "race_points": float(r.get("points", 0)),
            "sprint_points": 0,
            "points": float(r.get("points", 0))
        })

    season_data.append({
        "round": round_num,
        "grand_prix": race_name,
        "race_id": None,
        "slug": race_name.lower().replace(" grand prix", "").replace(" ", "-"),
        "fastest_lap_driver": fastest_driver,
        "fastest_lap_time": fastest_time,
        "results": results
    })


# -----------------------------
# SAVE FILE
# -----------------------------
final = {
    "season": SEASON,
    "last_updated": datetime.utcnow().isoformat(),
    "races": sorted(season_data, key=lambda x: x["round"])
}

with open(OUTPUT, "w") as f:
    json.dump(final, f, indent=2)

print("\nDONE:", len(final["races"]), "races saved")
