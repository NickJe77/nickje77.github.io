import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path

SEASON = 2026

INDEX = Path("docs/data/nrl/index.json")
MATCH_DIR = Path(f"docs/data/nrl/matches/{SEASON}")
MATCH_DIR.mkdir(parents=True, exist_ok=True)

URL = f"https://www.rugbyleagueproject.org/seasons/nrl-{SEASON}/results.html"

print("Downloading results page...")

headers = {"User-Agent": "Mozilla/5.0"}

r = requests.get(URL, headers=headers, timeout=30)
soup = BeautifulSoup(r.text, "html.parser")

games = []

rows = soup.select("table tbody tr")

for row in rows:

    cols = [c.get_text(strip=True) for c in row.find_all("td")]

    if len(cols) < 6:
        continue

    try:
        date = cols[0]
        home = cols[1]
        score = cols[2]
        away = cols[3]
        venue = cols[5]

        if "-" not in score:
            continue

        home_score, away_score = score.split("-")

        game_id = f"{date}-{home[:3]}-{away[:3]}".replace(" ", "")

        game = {
            "game_id": game_id,
            "date": date,
            "venue": venue,
            "home_team": home,
            "away_team": away,
            "home_score": int(home_score),
            "away_score": int(away_score),
            "players": []
        }

        games.append(game)

    except:
        continue

print("Games detected:", len(games))


# load index
if INDEX.exists():
    with open(INDEX) as f:
        index = json.load(f)
else:
    index = {"season": SEASON, "games": []}


new_games = 0

for g in games:

    game_id = g["game_id"]
    file = MATCH_DIR / f"{game_id}.json"

    if not file.exists():

        with open(file, "w") as f:
            json.dump(g, f, indent=2)

        if game_id not in index["games"]:
            index["games"].append(game_id)

        new_games += 1


index["games"] = sorted(index["games"])

with open(INDEX, "w") as f:
    json.dump(index, f, indent=2)

print("New games added:", new_games)
