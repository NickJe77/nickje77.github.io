import json
import re
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from collections import defaultdict

print("AFL REBUILD (AFLTABLES WORKING VERSION)")

SEASON = 2026
BASE = "https://afltables.com/afl/seas"

DATA_DIR = Path("docs/data/afl")
OUTPUT = DATA_DIR / f"afl_{SEASON}.json"
PLAYERS_DIR = DATA_DIR / "players"
PLAYERS_JSON = DATA_DIR / "players.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)
PLAYERS_DIR.mkdir(parents=True, exist_ok=True)


# -------------------------------
# HELPERS
# -------------------------------
def clean(x):
    return re.sub(r"\s+", " ", (x or "")).strip()


def to_int(x):
    try:
        return int(clean(x))
    except:
        return 0


# -------------------------------
# LOAD SEASON PAGE
# -------------------------------
url = f"{BASE}/{SEASON}.html"
print("Loading:", url)

html = requests.get(url).text
soup = BeautifulSoup(html, "html.parser")

tables = soup.find_all("table")

all_rows = []
match_id = 0


# -------------------------------
# PARSE TABLES (FIXED)
# -------------------------------
for table in tables:
    rows = table.find_all("tr")

    # skip junk tables
    if len(rows) < 20:
        continue

    # check if it looks like a player table
    first_data_row = rows[1].find_all("td")
    if len(first_data_row) < 10:
        continue

    match_id += 1

    for tr in rows[1:]:
        cols = tr.find_all("td")

        if len(cols) < 10:
            continue

        name = clean(cols[0].text)

        if not name or name.lower() == "player":
            continue

        row = {
            "match_id": f"{SEASON}_{match_id:04d}",
            "player": name,
            "season": SEASON,
            "round": None,
            "played_for": None,
            "played_against": None,

            "K": to_int(cols[1].text),
            "HB": to_int(cols[2].text),
            "D": to_int(cols[3].text),
            "M": to_int(cols[4].text),
            "G": to_int(cols[5].text),
            "B": to_int(cols[6].text),
        }

        all_rows.append(row)


print("TOTAL ROWS:", len(all_rows))


# -------------------------------
# SAVE MATCH DATA
# -------------------------------
OUTPUT.write_text(json.dumps(all_rows, indent=2))
print("✅ MATCH DATA SAVED")


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


# -------------------------------
# SAVE PLAYERS
# -------------------------------
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

print("✅ PLAYERS BUILT")
print("✅ REBUILD COMPLETE")
