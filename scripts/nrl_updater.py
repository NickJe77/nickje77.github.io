import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path

print("NRL FULL PLAYER STATS UPDATER")

SEASON = 2026
BASE = "https://afltables.com/rl/"

OUTPUT = Path("docs/data/nrl/2026.json")

HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_full_name(url):

    try:

        html = requests.get(url, headers=HEADERS, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")

        title = soup.find("title").text

        name = title.split(" - ")[0]

        return name

    except:
        return None


print("Downloading season page")

season_html = requests.get(f"{BASE}seas/{SEASON}.html", headers=HEADERS).text
season_soup = BeautifulSoup(season_html, "html.parser")

links = []

for a in season_soup.find_all("a", href=True):

    if a.text.strip() == "Match details":

        href = a["href"]

        if not href.startswith("http"):
            href = BASE + href.replace("../","")

        links.append(href)

links = sorted(set(links))

print("Match pages found:", len(links))

games = []

for link in links:

    match_id = link.split("/")[-1].replace(".html","")

    print("Processing", match_id)

    html = requests.get(link, headers=HEADERS).text
    soup = BeautifulSoup(html, "html.parser")

    players = []

    for row in soup.find_all("tr"):

        cols = row.find_all("td")

        if len(cols) < 5:
            continue

        name_cell = cols[0]

        player = name_cell.get_text(strip=True)

        a = name_cell.find("a")

        if a:

            url = a["href"]

            if not url.startswith("http"):
                url = BASE + url.replace("../","")

            full = get_full_name(url)

            if full:
                player = full

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
            pts = int(cols[4].text.strip())
        except:
            pts = 0

        players.append({
            "player": player,
            "tries": tries,
            "goals": goals,
            "field_goals": fg,
            "points": pts
        })

    games.append({
        "match_id": match_id,
        "season": SEASON,
        "players": players
    })

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with open(OUTPUT, "w") as f:
    json.dump(games, f, indent=2)

print("Matches processed:", len(games))
print("File written:", OUTPUT)
print("Updater complete")
