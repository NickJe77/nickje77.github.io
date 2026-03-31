import json
from pathlib import Path

print("BUILD PLAYER MAP FROM EXISTING DATA (NO API, NO CHANGES)")

BOX_DIR = Path("docs/data/baseball/boxscores/2026")
OUT = Path("docs/data/baseball/players.json")

players = {}

files = list(BOX_DIR.glob("*.json"))

if not files:
    print("NO FILES FOUND — STOP")
    exit()

print(f"Scanning {len(files)} games")

for file in files:
    try:
        with open(file) as f:
            data = json.load(f)

        # MLB boxscore structure
        teams = data.get("teams", {})

        for side in ["home", "away"]:
            team = teams.get(side, {})

            for p in team.get("players", {}).values():
                try:
                    pid = str(p["person"]["id"])
                    name = p["person"]["fullName"]

                    players[pid] = name
                except:
                    continue

    except:
        continue


if not players:
    print("NO PLAYERS FOUND — STOP")
    exit()

out = [{"player_id": k, "name": v} for k, v in players.items()]

with open(OUT, "w") as f:
    json.dump(out, f, indent=2)

print(f"Saved {len(out)} players")
