import requests, os, sys, json
from bs4 import BeautifulSoup

season = sys.argv[1]

BASE = "https://www.pro-football-reference.com"

print("Fetching games via boxscore index:", season)

games = []

# 🔥 iterate months (PFR splits schedule by month)
months = [
    "september", "october", "november",
    "december", "january", "february"
]

for m in months:

    url = f"{BASE}/years/{season}/{m}.htm"

    res = requests.get(url, headers={"User-Agent":"Mozilla/5.0"})

    if res.status_code != 200:
        continue

    soup = BeautifulSoup(res.text, "html.parser")

    for link in soup.find_all("a", href=True):

        href = link["href"]

        if "/boxscores/" not in href:
            continue

        game_id = href.split("/")[-1].replace(".htm","")

        games.append({
            "game_id": game_id,
            "url": BASE + href
        })

print("Games found:", len(games))

# remove duplicates
seen = set()
unique_games = []

for g in games:
    if g["game_id"] not in seen:
        seen.add(g["game_id"])
        unique_games.append(g)

os.makedirs("docs/data/nfl/raw", exist_ok=True)

with open(f"docs/data/nfl/raw/{season}_games.json","w") as f:
    json.dump(unique_games, f)
