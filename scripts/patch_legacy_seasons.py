import json
import os

BASE = "docs/data/baseball/seasons"

for filename in os.listdir(BASE):

    if not filename.endswith(".json"):
        continue

    season = filename.replace(".json", "")
    path = os.path.join(BASE, filename)

    with open(path, "r") as f:
        games = json.load(f)

    changed = 0

    for game in games:

        if not game.get("game_file"):

            date = game.get("date", "").replace("/", "-")
            away = game.get("away_team", "")
            home = game.get("home_team", "")

            if date and away and home:
                game["game_file"] = f"{date}_{away}_{home}.json"
                changed += 1

    with open(path, "w") as f:
        json.dump(games, f, ensure_ascii=False, indent=2)

    print(f"{season}: patched {changed} games")

print("Done")
