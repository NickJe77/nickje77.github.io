import json
from pathlib import Path

print("ADDING MISSING HEADER TO 2026 FILES")

BOX_DIR = Path("docs/data/baseball/boxscores/2026")

files = list(BOX_DIR.glob("*.json"))

for file in files:

    with open(file) as f:
        data = json.load(f)

    events = data.get("events", [])

    if not events:
        continue

    game_id = data["game_id"]
    date = data["date"].replace("-", "/")
    home = data["home_code"]
    away = data["away_code"]

    # -------------------------
    # BUILD HEADER
    # -------------------------
    header = [
        ["id", game_id],
        ["version", "2"],
        ["info", "visteam", away],
        ["info", "hometeam", home],
        ["info", "date", date]
    ]

    # -------------------------
    # MERGE
    # -------------------------
    data["events"] = header + events

    with open(file, "w") as f:
        json.dump(data, f, indent=2)

print("DONE — HEADERS ADDED")
