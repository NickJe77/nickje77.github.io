import json
from pathlib import Path

print("FIXING 2026 FILES TO MATCH 2025 FORMAT")

BOX_DIR = Path("docs/data/baseball/boxscores/2026")

files = list(BOX_DIR.glob("*.json"))

if not files:
    print("NO FILES FOUND")
    exit()

print(f"Processing {len(files)} files")


# -------------------------
# SAFE FIELD GET
# -------------------------
def g(d, *keys):
    for k in keys:
        if isinstance(d, dict) and k in d:
            return d[k]
    return None


# -------------------------
# CONVERT ONE FILE
# -------------------------
def convert(data):

    # Already correct format → leave it
    if "events" in data:
        return data

    gamePk = str(data.get("gamePk") or data.get("game_id") or "")

    date = g(data, "gameDate", "date")
    if date and "T" in date:
        date = date.split("T")[0]

    teams = data.get("teams", {})

    home = g(teams.get("home", {}), "team", {}).get("abbreviation", "UNK")
    away = g(teams.get("away", {}), "team", {}).get("abbreviation", "UNK")

    # -------------------------
    # BUILD EVENTS
    # -------------------------
    events = []

    plays = data.get("liveData", {}).get("plays", {}).get("allPlays", [])

    for p in plays:
        try:
            inning = p["about"]["inning"]
            half = p["about"]["halfInning"]

            batter = p["matchup"]["batter"]["id"]
            result = p["result"]["eventType"]

            events.append([
                "play",
                str(inning),
                "0" if half == "top" else "1",
                str(batter),
                result
            ])
        except:
            continue

    return {
        "game_id": gamePk,
        "date": date,
        "season": 2026,
        "home_code": home,
        "away_code": away,
        "home_team": home,
        "away_team": away,
        "events": events
    }


# -------------------------
# MAIN
# -------------------------
fixed = 0

for file in files:
    try:
        with open(file) as f:
            data = json.load(f)

        new_data = convert(data)

        with open(file, "w") as f:
            json.dump(new_data, f, indent=2)

        fixed += 1

    except:
        continue

print(f"FIXED {fixed} FILES")
