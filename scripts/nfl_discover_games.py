import requests, os, sys, json
from bs4 import BeautifulSoup

season = sys.argv[1]

BASE = "https://www.pro-football-reference.com"
url = f"{BASE}/years/{season}/games.htm"

print("Fetching schedule:", season)

res = requests.get(url, headers={"User-Agent":"Mozilla/5.0"})
soup = BeautifulSoup(res.text, "html.parser")

games = []

table = soup.find("table", {"id": "games"})

if not table:
    print("No games table found")
    exit()

tbody = table.find("tbody")

for row in tbody.find_all("tr"):

    # skip headers
    if row.get("class") and "thead" in row.get("class"):
        continue

    cols = row.find_all("td")
    if len(cols) == 0:
        continue

    link = row.find("a", href=True)
    if not link:
        continue

    href = link["href"]

    if "/boxscores/" not in href:
        continue

    game_id = href.split("/")[-1].replace(".htm","")

    games.append({
        "game_id": game_id,
        "url": BASE + href
    })

print("Games found:", len(games))

os.makedirs("docs/data/nfl/raw", exist_ok=True)

with open(f"docs/data/nfl/raw/{season}_games.json","w") as f:
    json.dump(games, f)
