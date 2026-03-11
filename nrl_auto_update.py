import json
import requests
from pathlib import Path

SEASON = 2026

INDEX = Path("docs/data/nrl/index.json")
MATCH_DIR = Path(f"docs/data/nrl/matches/{SEASON}")
MATCH_DIR.mkdir(parents=True, exist_ok=True)

URL = f"https://www.nrl.com/api/matches?competition=111&season={SEASON}"

print("Downloading NRL matches...")

r = requests.get(URL, timeout=30)
data = r.json()

matches = data.get("matches", [])

print("Matches returned:", len(matches))

# load index
if INDEX.exists():
    with open(INDEX) as f:
        index = json.load(f)
else:
    index = {"season": SEASON, "games": []}

new_games = 0

for m in matches:

    if m["matchState"] != "played":
        continue

    game_id = str(m["matchId"])

    game = {
        "game_id": game_id,
        "date": m["scheduledStartTime"][:10],
        "round": m["roundNumber"],
        "venue": m["venue"]["name"],
        "home_team": m["homeTeam"]["nickName"],
        "away_team": m["awayTeam"]["nickName"],
        "home_score": m["homeTeam"]["score"],
        "away_score": m["awayTeam"]["score"],
        "players": []
    }

    file = MATCH_DIR / f"{game_id}.json"

    if not file.exists():

        with open(file, "w") as f:
            json.dump(game, f, indent=2)

        if game_id not in index["games"]:
            index["games"].append(game_id)

        new_games += 1

index["games"] = sorted(index["games"])

with open(INDEX, "w") as f:
    json.dump(index, f, indent=2)

print("New games added:", new_games)
