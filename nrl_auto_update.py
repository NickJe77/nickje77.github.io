import json
import requests
from pathlib import Path

SEASON = 2026

INDEX = Path("docs/data/nrl/index.json")
MATCH_DIR = Path(f"docs/data/nrl/matches/{SEASON}")
MATCH_DIR.mkdir(parents=True, exist_ok=True)

URL = f"https://www.nrl.com/draw/data?competition=111&season={SEASON}"

print("Downloading NRL matches...")

headers = {"User-Agent": "Mozilla/5.0"}

r = requests.get(URL, headers=headers, timeout=30)

if r.status_code != 200:
    print("Download failed:", r.status_code)
    exit()

data = r.json()

games = []

for m in data["fixtures"]:

    # skip unplayed games
    if m["matchState"] != "Played":
        continue

    home = m["homeTeam"]["nickName"]
    away = m["awayTeam"]["nickName"]

    home_score = m.get("homeScore", 0)
    away_score = m.get("awayScore", 0)

    date = m["clock"]["kickOffTimeLong"][:10]

    round_title = m["roundTitle"]
    round_num = int(round_title.replace("Round ", ""))

    venue = m["venue"]

    game_id = f"{SEASON}R{round_num:02d}{home[:3]}{away[:3]}".upper()

    game = {
        "game_id": game_id,
        "season": SEASON,
        "round": round_num,
        "date": date,
        "venue": venue,
        "home_team": home,
        "away_team": away,
        "home_score": home_score,
        "away_score": away_score,
        "players": []
    }

    games.append(game)

print("Games detected:", len(games))


# LOAD INDEX

if INDEX.exists():
    with open(INDEX) as f:
        index = json.load(f)
else:
    index = {"season": SEASON, "games": []}


new_games = 0

for g in games:

    game_id = g["game_id"]
    match_file = MATCH_DIR / f"{game_id}.json"

    if not match_file.exists():

        with open(match_file, "w") as f:
            json.dump(g, f, indent=2)

        if game_id not in index["games"]:
            index["games"].append(game_id)

        new_games += 1


index["games"] = sorted(index["games"])

with open(INDEX, "w") as f:
    json.dump(index, f, indent=2)


print("New games added:", new_games)
print("Update complete")
