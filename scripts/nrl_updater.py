import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path

print("NRL FULL PLAYER STATS UPDATER")

SEASON = 2026

BASE_URL = "https://afltables.com/rl/"
SEASON_URL = f"{BASE_URL}seas/{SEASON}.html"

DATA_PATH = Path("docs/data/nrl/matches")
DATA_PATH.mkdir(parents=True, exist_ok=True)

OUT_FILE = DATA_PATH / f"{SEASON}.json"

HEADERS = {"User-Agent": "Mozilla/5.0"}

print("Downloading season page")

season_html = requests.get(SEASON_URL, headers=HEADERS).text
season_soup = BeautifulSoup(season_html, "html.parser")

match_links = []

for a in season_soup.find_all("a"):
    if a.text.strip() == "Match details":
        href = a.get("href")

        if not href.startswith("http"):
            href = BASE_URL + href.replace("../","")

        match_links.append(href)

match_links = sorted(set(match_links))

print("Match pages found:", len(match_links))

games = []

for link in match_links:

    match_id = link.split("/")[-1].replace(".html","")

    print("Processing", match_id)

    html = requests.get(link, headers=HEADERS).text
    soup = BeautifulSoup(html, "html.parser")

    players = []

    tables = soup.find_all("table")

    for table in tables:

        for row in table.find_all("tr"):

            cols = row.find_all("td")

            if len(cols) < 5:
                continue

            name_cell = cols[0]
            name = name_cell.get_text(strip=True)

            player_link = name_cell.find("a")

            if player_link:

                url = player_link["href"]

                if not url.startswith("http"):
                    url = BASE_URL + url.replace("../","")

                try:
                    p_html = requests.get(url, headers=HEADERS).text
                    p_soup = BeautifulSoup(p_html, "html.parser")

                    h1 = p_soup.find("h1")

                    if h1:
                        name = h1.get_text(strip=True)

                except:
                    pass

            try:
                tries = int(cols[1].text.strip())
            except:
                tries = 0

            try:
                goals = int(cols[2].text.strip())
            except:
                goals = 0

            try:
                fg = int(cols[3].text.strip())
            except:
                fg = 0

            try:
                points = int(cols[4].text.strip())
            except:
                points = 0

            players.append({
                "player": name,
                "tries": tries,
                "goals": goals,
                "field_goals": fg,
                "points": points
            })

    games.append({
        "match_id": match_id,
        "season": SEASON,
        "players": players
    })

with open(OUT_FILE, "w") as f:
    json.dump(games, f, indent=2)

print("Matches processed:", len(games))
print("Updater complete")
