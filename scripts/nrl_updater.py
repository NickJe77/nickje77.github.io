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

links = []

for a in soup.find_all("a", href=True):
    if "games" in a["href"] and a["href"].endswith(".html"):
        if "/rl/games/" in a["href"]:
            links.append("https://afltables.com" + a["href"])

links = sorted(set(links))

print("Match pages found:", len(links))

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

for link in links:

    match_id = link.split("/")[-1].replace(".html","")

    print("Processing", match_id)

    game_html = requests.get(link, headers=HEADERS).text
    game_soup = BeautifulSoup(game_html, "html.parser")

    tables = game_soup.find_all("table")

    players = []

    for table in tables:

        rows_html = table.find_all("tr")

        for r in rows_html:

            cols = [c.get_text(strip=True) for c in r.find_all("td")]

            if len(cols) < 5:
                continue

            name = cols[0]

            if name.lower() == "player":
                continue

            try:
                tries = int(cols[1])
            except:
                tries = 0

            try:
                goals = int(cols[2])
            except:
                goals = 0

            try:
                field_goals = int(cols[3])
            except:
                field_goals = 0

            try:
                points = int(cols[4])
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

print("Matches processed:", len(links))
print("Matches added:", added)
print("Updater complete")
