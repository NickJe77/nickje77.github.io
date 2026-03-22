import json
import re
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from collections import defaultdict

print("AFL REBUILD (AFLTABLES VERSION)")

SEASON = 2026
BASE = "https://afltables.com/afl/seas"

DATA_DIR = Path("docs/data/afl")
OUTPUT = DATA_DIR / f"afl_{SEASON}.json"
PLAYERS_DIR = DATA_DIR / "players"
PLAYERS_JSON = DATA_DIR / "players.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)
PLAYERS_DIR.mkdir(parents=True, exist_ok=True)


def clean(x):
    return re.sub(r"\s+", " ", (x or "")).strip()


def to_int(x):
    try:
        return int(x)
    except:
        return 0


# -------------------------------
# GET SEASON PAGE
# -------------------------------
url = f"{BASE}/{SEASON}.html"
html = requests.get(url).text
soup = BeautifulSoup(html, "html.parser")

tables = soup.find_all("table")

all_rows = []
match_id = 0

for table in tables:
    rows = table.find_all("tr")

    if len(rows) < 10:
        continue

    headers = [clean(td.text) for td in rows[0].find_all("td")]

    if "K" not in headers:
        continue

    match_id += 1

    for tr in rows[1:]:
        cols = tr.find_all("td")

        if len(cols) < len(headers):
            continue

        player = clean(cols[0].text)
        if not player:
            continue

        row = {
            "match_id": f"{SEASON}_{match_id:04d}",
            "player": player,
            "season": SEASON,
        }

        for i, h in enumerate(headers):
            if i >= len(cols):
                continue
            row[h] = to_int(cols[i].text)

        all_rows.append(row)


print("TOTAL ROWS:", len(all_rows))


# -------------------------------
# SAVE MATCH DATA
# -------------------------------
OUTPUT.write_text(json.dumps(all_rows, indent=2))


# -------------------------------
# BUILD PLAYERS
# -------------------------------
players = {}

for r in all_rows:
    name = r["player"]

    if name not in players:
        players[name] = {
            "name": name,
            "games": [],
            "career": defaultdict(int),
        }

    players[name]["games"].append(r)

    for k, v in r.items():
        if isinstance(v, int):
            players[name]["career"][k] += v


summary = []

for name, p in players.items():
    slug = name.lower().replace(" ", "-")

    (PLAYERS_DIR / f"{slug}.json").write_text(json.dumps({
        "name": name,
        "career": dict(p["career"]),
        "games": p["games"]
    }, indent=2))

    summary.append({
        "name": name,
        "slug": slug,
        "games": len(p["games"])
    })

PLAYERS_JSON.write_text(json.dumps(summary, indent=2))

print("✅ REBUILD COMPLETE")
