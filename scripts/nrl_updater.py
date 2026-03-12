import json
import requests
from pathlib import Path
from bs4 import BeautifulSoup

print("NRL PLAYER STATS UPDATER")

SEASON = 2026

BASE = Path("docs/data/nrl")
MATCH_FILE = BASE / "matches" / f"{SEASON}.json"

BASE.mkdir(parents=True, exist_ok=True)
MATCH_FILE.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

season_url = f"https://afltables.com/rl/seas/{SEASON}.html"

print("Downloading season page")

html = requests.get(season_url, headers=HEADERS).text
soup = BeautifulSoup(html, "html.parser")

match_links = []

for a in soup.find_all("a", href=True):
    if "Match details" in a.text:
        href = a["href"]
        if not href.startswith("http"):
            href = "https://afltables.com/rl/" + href.replace("../","")
        match_links.append(href)

match_links = sorted(set(match_links))

print("Match pages found:", len(match_links))

rows = []

for link in match_links:

    match_id = link.split("/")[-1].replace(".html","")

    print("Processing", match_id)

    game_html = requests.get(link, headers=HEADERS).text
    game_soup = BeautifulSoup(game_html, "html.parser")

    players = []

    tables = game_soup.find_all("table")

    for table in tables:

        rows_html = table.find_all("tr")

        for r in rows_html:

            cols = r.find_all("td")

            if len(cols) < 5:
                continue

            name = cols[0].get_text(strip=True)

            try:
                tries = int(cols[1].get_text(strip=True))
            except:
                tries = 0

            try:
                goals = int(cols[2].get_text(strip=True))
            except:
                goals = 0

            try:
                field_goals = int(cols[3].get_text(strip=True))
            except:
                field_goals = 0

            try:
                points = int(cols[4].get_text(strip=True))
            except:
                points = 0

            players.append({
                "player": name,
                "tries": tries,
                "goals": goals,
                "field_goals": field_goals,
                "points": points
            })

    rows.append({
        "match_id": match_id,
        "season": SEASON,
        "players": players
    })

with open(MATCH_FILE, "w") as f:
    json.dump(rows, f, indent=2, sort_keys=True)

print("Matches processed:", len(rows))
print("Updater complete")
