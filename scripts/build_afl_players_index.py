import json
from pathlib import Path

PLAYERS_DIR = Path("docs/data/afl/players")
OUTPUT = Path("docs/data/afl/players/index.json")

players = []

for file in PLAYERS_DIR.glob("*.json"):
    try:
        data = json.loads(file.read_text(encoding="utf-8"))

        name = (
            data.get("name")
            or data.get("player")
            or file.stem.replace("-", " ").title()
        )

        players.append({
            "name": name,
            "file": file.name
        })

    except Exception as e:
        print("Skipping", file, e)

players = sorted(players, key=lambda x: x["name"])

OUTPUT.write_text(json.dumps(players, indent=2), encoding="utf-8")

print("Built index.json with", len(players), "players")
