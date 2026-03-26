import requests, os, sys, json, re
from bs4 import BeautifulSoup, Comment

season = sys.argv[1]

BASE = "https://www.pro-football-reference.com"
url = f"{BASE}/years/{season}/games.htm"

print("Fetching schedule:", season)

res = requests.get(url, headers={"User-Agent":"Mozilla/5.0"})
soup = BeautifulSoup(res.text, "html.parser")

# 🔥 STEP 1: find commented tables
comments = soup.find_all(string=lambda text: isinstance(text, Comment))

table = None

for c in comments:
    if 'id="games"' in c:
        table = BeautifulSoup(c, "html.parser").find("table", {"id": "games"})
        break

# fallback (in case it's not commented)
if not table:
    table = soup.find("table", {"id": "games"})

if not table:
    print("Still no games table found")
    exit()

games = []

for row in table.find("tbody").find_all("tr"):

    if row.get("class") and "thead" in row.get("class"):
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
