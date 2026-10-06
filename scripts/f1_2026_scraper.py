import requests
import json
import time
from pathlib import Path
from datetime import datetime

print("F1 2026 FINAL BUILDER (WITH SPRINT SUPPORT)")

BASE = "https://api.jolpi.ca/ergast/f1"
SEASON = 2026
OUTPUT = Path("docs/data/f1/2026.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)


def get_json(url, attempts=3):
    """Fetch JSON with a short pause before each call and a few retries.

    The script makes about two API calls per round, so a single hiccup
    must not silently drop a round (or a weekend's sprint points).
    """
    for attempt in range(1, attempts + 1):
        time.sleep(0.25)  # stay well inside the API's burst limit
        try:
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"ERROR (attempt {attempt}/{attempts}):", url, e)
            if attempt < attempts:
                time.sleep(2 * attempt)
    return None


# -----------------------------
# STATUS CLEANING
# -----------------------------
status_map = {
    "Accident": "DNF",
    "Collision": "DNF",
    "Collision damage": "DNF",
    "Engine": "DNF",
    "Gearbox": "DNF",
    "Hydraulics": "DNF",
    "Electrical": "DNF",
    "Spun off": "DNF",
    "Overheating": "DNF",
    "Mechanical": "DNF",
    "Brakes": "DNF",
    "Suspension": "DNF",
    "Tyre": "DNF",
    "Puncture": "DNF",
    "Power Unit": "DNF",
    "ERS": "DNF",
    "Did Not Finish": "DNF",
    "Retired": "DNF",
    "Did Not Start": "DNS",
    "Withdrawn": "DNS",
    "Disqualified": "DSQ",
}

def fix_driver_name(given, family):
    full = f"{given} {family}"
    name_overrides = {
        "Andrea Kimi Antonelli": "Kimi Antonelli",
    }
    return name_overrides.get(full, full)


def parse_results(result_list):
    """Parse a list of race or sprint result entries into our format."""
    results = []
    fastest_driver = None
    fastest_time = None

    for r in result_list:
        driver = r["Driver"]
        constructor = r["Constructor"]
        name = fix_driver_name(driver["givenName"], driver["familyName"])

        status = r.get("status", "")
        time_val = r.get("Time", {}).get("time", "")

        # Position + status
        raw_position = r.get("position", "0")
        if time_val:
            display_position = int(raw_position)
        else:
            mapped = status_map.get(status, status)
            display_position = mapped
            time_val = ""

        # Fastest lap (race only — sprints don't have fastest lap points)
        fl = r.get("FastestLap")
        if fl and fl.get("rank") == "1":
            fastest_driver = name
            fl_time = fl.get("Time", {})
            fastest_time = fl_time.get("time", "")

        results.append({
            "position": display_position,
            "driver": name,
            "team": constructor["name"],
            "grid": int(r.get("grid", 0)),
            "time": time_val,
            "points": float(r.get("points", 0)),
        })

    return results, fastest_driver, fastest_time


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
    print(f"\nRound {round_num} - {race_name}")

    # -----------------------------
    # RACE RESULTS
    # -----------------------------
    results_json = get_json(f"{BASE}/{SEASON}/{round_num}/results.json")
    if not results_json:
        print(f"  No race results for round {round_num}, skipping.")
        continue

    race_block = results_json["MRData"]["RaceTable"]["Races"]
    if not race_block:
        print(f"  Empty race results for round {round_num}, skipping.")
        continue

    race_results, fastest_driver, fastest_time = parse_results(race_block[0]["Results"])
    print(f"  Race: {len(race_results)} results")

    # -----------------------------
    # SPRINT RESULTS
    # -----------------------------
    # No hardcoded list of sprint rounds. The API is asked for sprint
    # results for EVERY round; non-sprint rounds simply come back empty.
    # (The old hardcoded list went stale: round numbers shift whenever the
    # calendar changes, and it had Belgium/Azerbaijan in and
    # Canada/Britain/Netherlands out.)
    sprint_results = []
    scheduled_sprint = "Sprint" in race  # calendar marks this as a sprint weekend

    sprint_json = get_json(f"{BASE}/{SEASON}/{round_num}/sprint.json")
    if sprint_json is None:
        print("  WARNING: sprint request failed -- sprint points for this round may be missing")
        sprint_block = []
    else:
        sprint_block = sprint_json["MRData"]["RaceTable"]["Races"]

    if sprint_block and "SprintResults" in sprint_block[0]:
        sprint_results, _, _ = parse_results(sprint_block[0]["SprintResults"])
        print(f"  Sprint: {len(sprint_results)} results")

        # Merge sprint points into race results by driver name
        sprint_points_map = {
            s["driver"]: s["points"] for s in sprint_results
        }
        for result in race_results:
            result["sprint_points"] = sprint_points_map.get(result["driver"], 0.0)
            result["points"] = result["race_points"] = result["points"]
            result["total_points"] = result["points"] + result["sprint_points"]
    elif scheduled_sprint:
        print("  WARNING: calendar lists a sprint for this round but no sprint results were returned")

    is_sprint_round = bool(sprint_results) or scheduled_sprint

    # Fill in sprint_points = 0 for non-sprint rounds or if sprint not yet run
    for result in race_results:
        if "sprint_points" not in result:
            result["sprint_points"] = 0.0
        if "race_points" not in result:
            result["race_points"] = result["points"]
        if "total_points" not in result:
            result["total_points"] = result["points"]

    season_data.append({
        "round": round_num,
        "grand_prix": race_name,
        "race_id": None,
        "slug": race_name.lower().replace(" grand prix", "").replace(" ", "-"),
        "is_sprint_round": is_sprint_round,
        "fastest_lap_driver": fastest_driver,
        "fastest_lap_time": fastest_time,
        "results": race_results,
        "sprint_results": sprint_results,
    })

# -----------------------------
# SAVE FILE
# -----------------------------
final = {
    "season": SEASON,
    "last_updated": datetime.utcnow().isoformat(),
    "races": sorted(season_data, key=lambda x: x["round"]),
}

with open(OUTPUT, "w") as f:
    json.dump(final, f, indent=2)

print(f"\nDONE: {len(final['races'])} races saved to {OUTPUT}")
