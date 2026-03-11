import json
import requests
from pathlib import Path
from bs4 import BeautifulSoup

SEASON = 2026

INDEX_PATH = Path("docs/data/nrl/index.json")
MATCH_DIR = Path(f"docs/data/nrl/matches/{SEASON}")

MATCH_DIR.mkdir(parents=True, exist_ok=True)

URL = "https://www.nrl.com/draw/"

print("Downloading NRL draw page...")

res = requests.get(URL, timeout=20)
soup = BeautifulSoup(res.text, "html.parser")

games_found = []

for match in soup.select(".match-card"):

    try:
        teams = match.select(".match-team__name")
        scores = match.select(".match-team__score")
        venue = match.select_one(".match-venue").text.strip()
        date = match.select_one(".match-date").text.strip()

        home_team = teams[0].text.strip()
        away_team = teams[1].text.strip()

        home_score = int(scores[0].text.strip())
        away_score = int(scores[1].text.strip())

        game_id = f"{date}-{home_team[:3]}-{away_team[:3]}".replace(" ","")

        game = {
            "game_id": game_id,
            "date": date,
            "venue": venue,
            "home_team": home_team,
            "away_team": away_team,
            "home_score": home_score,
            "away_score": away_score,
            "players": []
        }

        games_found.append(game)

    except:
        continue

print("Games found:", len(games_found))

# load index
if INDEX_PATH.exists():
    with open(INDEX_PATH) as f:
        index = json.load(f)
else:
    index = {"season": SEASON, "games": []}

new_games = 0

for game in games_found:

    game_id = game["game_id"]
    file_path = MATCH_DIR / f"{game_id}.json"

    if not file_path.exists():

        with open(file_path, "w") as f:
            json.dump(game, f, indent=2)

        index["games"].append(game_id)
        new_games += 1

index["games"] = sorted(index["games"])

with open(INDEX_PATH, "w") as f:
    json.dump(index, f, indent=2)

print("New games added:", new_games)
