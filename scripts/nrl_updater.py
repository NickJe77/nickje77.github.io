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

existing = []

if MATCH_FILE.exists():
    try:
        with open(MATCH_FILE) as f:
            existing = json.load(f)
    except:
        existing = []

rows = existing.copy()

existing_ids = {m.get("match_id") for m in existing}

added = 0

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

            name_cell = cols[0]

            name = name_cell.get_text(strip=True)

            # try to get full name if player page exists
            a = name_cell.find("a")
            if a and a.get("href"):

                player_url = a["href"]

                if not player_url.startswith("http"):
                    player_url = "https://afltables.com/rl/" + player_url.replace("../","")

                try:
                    p_html = requests.get(player_url, headers=HEADERS).text
                    p_soup = BeautifulSoup(p_html, "html.parser")

                    h1 = p_soup.find("h1")
                    if h1:
                        name = h1.get_text(strip=True)

                except:
                    pass

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

    if not players:
        continue

    game = {
        "season": SEASON,
        "match_id": match_id,
        "players": players
    }

    found = False

    for e in rows:
        if e.get("match_id") == match_id:
            e.update(game)
            found = True
            break

    if not found:
        rows.append(game)
        added += 1

with open(MATCH_FILE, "w") as f:
    json.dump(rows, f, indent=2, sort_keys=True)

print("Matches processed:", len(match_links))
print("Matches added:", added)
print("Updater complete")
