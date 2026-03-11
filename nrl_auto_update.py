import json
import re
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

if r.status_code != 200:
    print("Failed to download page:", r.status_code)
    exit()

soup = BeautifulSoup(r.text, "html.parser")

games = []

rows = soup.find_all("tr")

for row in rows:

    text = row.get_text(" ", strip=True)

    # detect score pattern like 24-18
    score_match = re.search(r"\b\d+\-\d+\b", text)

    if not score_match:
        continue

    try:

        cols = [c.get_text(strip=True) for c in row.find_all("td")]

        date = cols[0]
        home = cols[1]
        score = cols[2]
        away = cols[3]

        venue = ""
        if len(cols) > 5:
            venue = cols[5]

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


# LOAD INDEX

if INDEX.exists():
    with open(INDEX) as f:
        index = json.load(f)
else:
    index = {"season": SEASON, "games": []}


# ADD NEW GAMES

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
