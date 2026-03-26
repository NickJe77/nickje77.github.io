import requests, os, sys, json
from bs4 import BeautifulSoup

season = sys.argv[1]

BASE = "https://www.pro-football-reference.com"
url = f"{BASE}/years/{season}/games.htm"

print("Fetching schedule:", season)

res = requests.get(url, headers={"User-Agent":"Mozilla/5.0"})
soup = BeautifulSoup(res.text, "html.parser")

games = []

for row in soup.select("#games tbody tr"):
    if "class" in row.attrs and "thead" in row.attrs["class"]:
        continue

    link = row.find("a", href=True)
    if not link:
        continue

    game_id = link["href"].split("/")[-1].replace(".htm","")

    games.append({
        "game_id": game_id,
        "url": BASE + link["href"]
    })

os.makedirs("docs/data/nfl/raw", exist_ok=True)

with open(f"docs/data/nfl/raw/{season}_games.json","w") as f:
    json.dump(games, f)

print("Games found:", len(games))
