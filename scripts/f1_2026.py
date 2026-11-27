import json
import sys
import time
from datetime import datetime, date, timezone
from pathlib import Path

import requests

print("F1 2026 FINAL BUILDER (WITH SPRINT SUPPORT)")

BASE = "https://api.jolpi.ca/ergast/f1"
SEASON = 2026
OUTPUT = Path("docs/data/f1/2026.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

# Jolpica allows 4 requests/second burst and 500/hour sustained.
# Stay comfortably under the burst limit.
REQUEST_GAP = 0.35
MAX_RETRIES = 5

session = requests.Session()
session.headers["User-Agent"] = "f1-2026-scraper (GitHub Actions)"
_last_request = 0.0


class FetchError(Exception):
    pass


def get_json(url):
    """GET a URL, pacing requests and retrying on rate limits / server errors.

    Raises FetchError if it still fails, instead of returning None, so a
    failure can never be mistaken for "no results yet".
    """
    global _last_request
    for attempt in range(1, MAX_RETRIES + 1):
        wait = REQUEST_GAP - (time.monotonic() - _last_request)
        if wait > 0:
            time.sleep(wait)
        _last_request = time.monotonic()

        try:
            r = session.get(url, timeout=20)
        except requests.RequestException as e:
            reason = str(e)
            backoff = 2 ** attempt
        else:
            if r.status_code == 200:
                return r.json()
            reason = f"HTTP {r.status_code}"
            if r.status_code == 429 or r.status_code >= 500:
                retry_after = r.headers.get("Retry-After", "")
                backoff = int(retry_after) if retry_after.isdigit() else 2 ** attempt
            else:
                raise FetchError(f"{url}: {reason}")

        print(f"  retry {attempt}/{MAX_RETRIES} for {url} ({reason}), waiting {backoff}s")
        time.sleep(backoff)

    raise FetchError(f"{url}: gave up after {MAX_RETRIES} attempts ({reason})")


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

        raw_position = r.get("position", "0")
        if time_val:
            display_position = int(raw_position)
        else:
            display_position = status_map.get(status, status)
            time_val = ""

        fl = r.get("FastestLap")
        if fl and fl.get("rank") == "1":
            fastest_driver = name
            fastest_time = fl.get("Time", {}).get("time", "")

        results.append({
            "position": display_position,
            "driver": name,
            "team": constructor["name"],
            "grid": int(r.get("grid", 0)),
            "time": time_val,
            "points": float(r.get("points", 0)),
        })

    return results, fastest_driver, fastest_time


def race_has_started(race):
    """True if the race start time is in the past (UTC)."""
    d = race.get("date")
    if not d:
        return True
    t = race.get("time", "00:00:00Z").replace("Z", "+00:00")
    try:
        start = datetime.fromisoformat(f"{d}T{t}")
    except ValueError:
        return date.fromisoformat(d) <= datetime.now(timezone.utc).date()
    return start <= datetime.now(timezone.utc)


# -----------------------------
# LOAD EXISTING DATA
# Rounds we fail to fetch keep their previous data instead of vanishing.
# -----------------------------
existing = {}
if OUTPUT.exists():
    try:
        for r in json.loads(OUTPUT.read_text()).get("races", []):
            existing[r["round"]] = r
    except (json.JSONDecodeError, KeyError) as e:
        print(f"WARNING: could not read existing {OUTPUT}: {e}")

# -----------------------------
# GET RACE CALENDAR
# -----------------------------
try:
    calendar = get_json(f"{BASE}/{SEASON}.json?limit=100")
except FetchError as e:
    print("FAILED TO LOAD CALENDAR:", e)
    sys.exit(1)

races = calendar["MRData"]["RaceTable"]["Races"]
print(f"Calendar: {len(races)} rounds")

season_data = {}
failed = []        # rounds that should have results but couldn't be fetched
not_yet = []       # rounds that have run but have no results published yet

for race in races:
    round_num = int(race["round"])
    race_name = race["raceName"]
    # The calendar itself says which weekends have a sprint, so no
    # hard-coded list to keep in sync when rounds get moved or cancelled.
    is_sprint_round = "Sprint" in race
    print(f"\nRound {round_num} - {race_name}{' (sprint)' if is_sprint_round else ''}")

    if not race_has_started(race):
        print("  Not raced yet, skipping.")
        continue

    try:
        results_json = get_json(f"{BASE}/{SEASON}/{round_num}/results.json?limit=100")
        race_block = results_json["MRData"]["RaceTable"]["Races"]
        if not race_block or not race_block[0].get("Results"):
            print("  No race results published yet.")
            not_yet.append(round_num)
            if round_num in existing:
                season_data[round_num] = existing[round_num]
            continue

        race_results, fastest_driver, fastest_time = parse_results(race_block[0]["Results"])
        print(f"  Race: {len(race_results)} results")

        # Ask for sprint results on every raced round, so a sprint is never
        # missed even if the calendar doesn't flag it. Non-sprint rounds
        # simply come back empty.
        sprint_results = []
        sprint_json = get_json(f"{BASE}/{SEASON}/{round_num}/sprint.json?limit=100")
        sprint_block = sprint_json["MRData"]["RaceTable"]["Races"]
        if sprint_block and sprint_block[0].get("SprintResults"):
            sprint_results, _, _ = parse_results(sprint_block[0]["SprintResults"])
            print(f"  Sprint: {len(sprint_results)} results")
        elif is_sprint_round:
            print("  WARNING: calendar lists a sprint but no sprint results were returned")
        is_sprint_round = is_sprint_round or bool(sprint_results)

    except FetchError as e:
        print(f"  ERROR: {e}")
        failed.append(round_num)
        if round_num in existing:
            print("  Keeping previously saved data for this round.")
            season_data[round_num] = existing[round_num]
        continue

    sprint_points_map = {s["driver"]: s["points"] for s in sprint_results}
    for result in race_results:
        result["race_points"] = result["points"]
        result["sprint_points"] = sprint_points_map.get(result["driver"], 0.0)
        result["total_points"] = result["race_points"] + result["sprint_points"]

    season_data[round_num] = {
        "round": round_num,
        "grand_prix": race_name,
        "race_id": None,
        "slug": race_name.lower().replace(" grand prix", "").replace(" ", "-"),
        "is_sprint_round": is_sprint_round,
        "fastest_lap_driver": fastest_driver,
        "fastest_lap_time": fastest_time,
        "results": race_results,
        "sprint_results": sprint_results,
    }

# -----------------------------
# SAVE FILE
# -----------------------------
final = {
    "season": SEASON,
    "last_updated": datetime.now(timezone.utc).isoformat(),
    "races": [season_data[k] for k in sorted(season_data)],
}

with open(OUTPUT, "w") as f:
    json.dump(final, f, indent=2)

print(f"\nDONE: {len(final['races'])} races saved to {OUTPUT}")
if not_yet:
    print(f"Raced but no results published yet: rounds {not_yet}")

# Fail the workflow if anything went wrong, so a green tick means it really worked.
if failed:
    print(f"FAILED to fetch rounds {failed}; see errors above.")
    sys.exit(1)
