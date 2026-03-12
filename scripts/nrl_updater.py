import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path

print("NRL FULL PLAYER STATS UPDATER")

SEASON = 2026
BASE = "https://afltables.com/rl/"

OUTPUT_FILE = Path("docs/data/nrl/2026.json")

HEADERS = {"User-Agent": "Mozilla/5.0"}

season_url = f"{BASE}seas/{SEASON}.html"

print("Downloading season page")

html = requests.get(season_url, headers=HEADERS).text
soup = BeautifulSoup(html, "html.parser")

match_links = []

for a in soup.find_all("a", href=True):
    if a.text.strip() == "Match details":
        href = a["href"]

        if not href.startswith("http"):
            href = BASE + href.replace("../", "")

        match_links.append(href)

match_links = sorted(set(match_links))

print("Match pages found:", len(match_links))

games = []

for link in match_links:

    match_id = link.split("/")[-1].replace(".html","")

    print("Processing", match_id)

    game_html = requests.get(link, headers=HEADERS).text
    game_soup = BeautifulSoup(game_html, "html.parser")

    players = []

    tables = game_soup.find_all("table")

    for table in tables:
        for row in table.find_all("tr"):

            cols = row.find_all("td")

            if len(cols) < 5:
                continue

            name_cell = cols[0]
            player_name = name_cell.get_text(strip=True)

            link_tag = name_cell.find("a")

            if link_tag and link_tag.get("href"):

                player_url = link_tag["href"]

                if not player_url.startswith("http"):
                    player_url = BASE + player_url.replace("../","")

                try:
                    p_html = requests.get(player_url, headers=HEADERS).text
                    p_soup = BeautifulSoup(p_html, "html.parser")

                    h1 = p_soup.find("h1")

                    if h1:
                        player_name = h1.get_text(strip=True)

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
                "player": player_name,
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

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

with open(OUTPUT_FILE, "w") as f:
    json.dump(games, f, indent=2)

print("Matches processed:", len(games))
print("File written:", OUTPUT_FILE)
print("Updater complete")
