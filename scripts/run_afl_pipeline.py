import json
import re
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from collections import defaultdict
from urllib.parse import urljoin

print("AFL REBUILD (AFLTABLES FINAL FIXED VERSION)")

SEASON = 2026
BASE = "https://afltables.com/afl/seas/"

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
# GET MATCH LINKS (FIXED)
# -------------------------------
season_url = f"{BASE}{SEASON}.html"
print("Loading:", season_url)

html = requests.get(season_url).text
soup = BeautifulSoup(html, "html.parser")

links = []

for a in soup.find_all("a", href=True):
    href = a["href"]

    if "stats/games" not in href:
        continue

    full_url = urljoin(season_url, href)
    links.append(full_url)

links = sorted(set(links))

print("MATCHES FOUND:", len(links))


# -------------------------------
# PARSE MATCHES
# -------------------------------
all_rows = []
match_id = 0

for link in links:
    match_id += 1
    print("Match:", match_id)

    try:
        html = requests.get(link).text
        soup = BeautifulSoup(html, "html.parser")
    except Exception as e:
        print("FAILED:", link)
        continue

    tables = soup.find_all("table")

    for table in tables:
        rows = table.find_all("tr")

        if len(rows) < 15:
            continue

        # 🔥 detect correct player stat tables
        header = [clean(td.text) for td in rows[0].find_all("td")]

        if "K" not in header or "HB" not in header:
            continue

        for tr in rows[1:]:
            cols = tr.find_all("td")

            if len(cols) < 8:
                continue

            name = clean(cols[0].text)

            if not name or name.lower() == "player":
                continue

            row = {
                "match_id": f"{SEASON}_{match_id:04d}",
                "player": name,
                "season": SEASON,

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
