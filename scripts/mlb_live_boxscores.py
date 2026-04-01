import json
from pathlib import Path

print("CONVERTING 2026 → MATCH 2025 FORMAT")

BOX_DIR = Path("docs/data/baseball/boxscores/2026")


# -------------------------
# LOAD PLAYER MAP
# -------------------------
# You MUST have this file (we built earlier)
PLAYER_MAP_FILE = Path("docs/data/baseball/players.json")

player_map = {}

if PLAYER_MAP_FILE.exists():
    with open(PLAYER_MAP_FILE) as f:
        data = json.load(f)
        for p in data:
            player_map[str(p["player_id"])] = p["name"]


# -------------------------
# SIMPLE EVENT TRANSLATION
# -------------------------
def convert_event(desc):

    d = desc.lower()

    # basic mappings (expand later)
    if "single" in d:
        return ["11", "CBX", "S"]
    if "double" in d:
        return ["20", "CBX", "D"]
    if "triple" in d:
        return ["30", "CBX", "T"]
    if "home run" in d:
        return ["40", "CBX", "HR"]
    if "strikeout" in d:
        return ["K", "CBX", "K"]
    if "walk" in d:
        return ["W", "CBX", "BB"]

    return ["00", "CBX", "UNK"]


# -------------------------
# PROCESS FILES
# -------------------------
files = list(BOX_DIR.glob("*.json"))

for file in files:

    with open(file) as f:
        data = json.load(f)

    new_events = []

    for e in data.get("events", []):

        try:
            pid = e[3]
            desc = e[4]

            short_id = player_map.get(pid, pid)

            codes = convert_event(desc)

            new_events.append([
                "play",
                e[1],
                e[2],
                short_id,
                codes[0],
                codes[1],
                codes[2]
            ])
        except:
            continue

    data["events"] = new_events

    with open(file, "w") as f:
        json.dump(data, f, indent=2)

print("DONE — NOW MATCHES 2025 STRUCTURE")
