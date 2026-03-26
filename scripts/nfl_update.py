import os
import sys
import json
import time
import requests
from bs4 import BeautifulSoup

BASE = "https://www.pro-football-reference.com"

season = sys.argv[1]

SEASON_DIR = f"docs/data/nfl/seasons"
GAME_DIR = f"docs/data/nfl/games/{season}"

os.makedirs(SEASON_DIR, exist_ok=True)
os.makedirs(GAME_DIR, exist_ok=True)

season_file = f"{SEASON_DIR}/{season}.json"

# -----------------------
# LOAD EXISTING
# -----------------------
existing_games = set()

if os.path.exists(season_file):
    try:
        data = json.load(open(season_file))
        for g in data.get("games", []):
            existing_games.add(g["game_id"])
    except:
        pass


# -----------------------
# GET SCHEDULE PAGE
# -----------------------
url = f"{BASE}/years/{season}/games.htm"

print("Fetching season:", season)

res = requests.get(url, headers={"User-Agent":"Mozilla/5.0"})
soup = BeautifulSoup(res.text, "html.parser")

rows = soup.select("#games tbody tr")

season_games = []

for row in rows:

    if "class" in row.attrs and "thead" in row.attrs["class"]:
        continue

    cols = row.find_all("td")
    if not cols:
        continue

    link = row.find("a", href=True)
    if not link:
        continue

    game_url = BASE + link["href"]
    game_id = link["href"].split("/")[-1].replace(".htm","")

    if game_id in existing_games:
        print("Skipping existing:", game_id)
        continue

    print("Scraping:", game_id)

    try:
        r = requests.get(game_url, headers={"User-Agent":"Mozilla/5.0"})
        gsoup = BeautifulSoup(r.text, "html.parser")

        teams = gsoup.select("div.scorebox strong a")
        scores = gsoup.select("div.scorebox div.score")

        away_team = teams[0].text
        home_team = teams[1].text

        away_score = int(scores[0].text)
        home_score = int(scores[1].text)

        game_data = {
            "game_id": game_id,
            "url": game_url,
            "home_team": home_team,
            "away_team": away_team,
            "home_score": home_score,
            "away_score": away_score
        }

        # SAVE GAME FILE
        with open(f"{GAME_DIR}/{game_id}.json", "w") as f:
            json.dump(game_data, f)

        season_games.append({
            "game_id": game_id,
            "home_team": home_team,
            "away_team": away_team,
            "home_score": home_score,
            "away_score": away_score
        })

        time.sleep(2)

    except Exception as e:
        print("Failed:", game_id, e)


# -----------------------
# UPDATE SEASON FILE
# -----------------------
existing_list = []

if os.path.exists(season_file):
    try:
        existing_list = json.load(open(season_file)).get("games", [])
    except:
        pass

combined = existing_list + season_games

with open(season_file, "w") as f:
    json.dump({"season": int(season), "games": combined}, f)

print("Done:", season)
