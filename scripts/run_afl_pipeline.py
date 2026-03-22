import json
import re
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from collections import defaultdict
from urllib.parse import urljoin

print("AFL REBUILD (STRUCTURED MATCH VERSION)")

SEASON = 2026
BASE = "https://afltables.com/afl/seas/"

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
        return int(clean(x))
    except:
        return 0


def safe_slug(name):
    slug = name.lower().replace(" ", "-")
    slug = re.sub(r"[^a-z0-9\-]", "", slug)
    return slug[:60]


# -------------------------------
# GET MATCH LINKS
# -------------------------------
season_url = f"{BASE}{SEASON}.html"
html = requests.get(season_url).text
soup = BeautifulSoup(html, "html.parser")

links = []

for a in soup.find_all("a", href=True):
    if "stats/games" in a["href"]:
        links.append(urljoin(season_url, a["href"]))

links = sorted(set(links))

print("MATCHES:", len(links))


# -------------------------------
# PARSE MATCHES
# -------------------------------
all_rows = []
match_id = 0

for link in links:
    match_id += 1
    print("Match:", match_id)

    html = requests.get(link).text
    soup = BeautifulSoup(html, "html.parser")

    text = soup.get_text(" ")

    # -------------------------------
    # MATCH META (ROUGH BUT WORKING)
    # -------------------------------
    teams = re.findall(r"\b[A-Z][a-z]+\b", text)

    home_team = teams[0] if len(teams) > 1 else ""
    away_team = teams[1] if len(teams) > 1 else ""

    venue = ""
    venue_match = re.search(r"Venue:\s*([A-Za-z\s\.]+)", text)
    if venue_match:
        venue = venue_match.group(1).strip()

    crowd = 0
    crowd_match = re.search(r"Attendance:\s*(\d+)", text)
    if crowd_match:
        crowd = int(crowd_match.group(1))

    date = ""
    date_match = re.search(r"\w{3}\s\d{1,2}\s\w+\s\d{1,2}:\d{2}", text)
    if date_match:
        date = date_match.group(0)

    # -------------------------------
    # PLAYER TABLES
    # -------------------------------
    tables = soup.find_all("table")

    for table in tables:
        rows = table.find_all("tr")

        if len(rows) < 10:
            continue

        for tr in rows:
            cols = tr.find_all("td")

            if len(cols) < 15:
                continue

            name = clean(cols[0].text)

            # strict player filter
            if (
                not name
                or "quarter" in name.lower()
                or "goal" in name.lower()
                or "behind" in name.lower()
                or "lead" in name.lower()
                or name.lower() in ["player", "totals", "opposition"]
            ):
                continue

            row = {
                "season": SEASON,
                "round": "",  # we’ll fix next step
                "venue": venue,
                "match_id": match_id,
                "player": name,
                "played_for": "",  # next step
                "played_against": "",

                "K": to_int(cols[1].text),
                "HB": to_int(cols[3].text),
                "D": to_int(cols[4].text),
                "M": to_int(cols[2].text),
                "G": to_int(cols[5].text),
                "B": to_int(cols[6].text),

                "T": to_int(cols[7].text),
                "HO": to_int(cols[8].text),
                "FF": to_int(cols[12].text),
                "FA": to_int(cols[13].text),

                "home_team": home_team,
                "away_team": away_team,
                "home_points": 0,
                "away_points": 0,
                "margin": 0,
                "total_points": 0,

                "home_q1": 0,
                "home_q2": 0,
                "home_q3": 0,
                "home_q4": 0,
                "away_q1": 0,
                "away_q2": 0,
                "away_q3": 0,
                "away_q4": 0,

                "crowd": crowd,
                "date": date,
                "date_iso": ""
            }

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
    slug = safe_slug(name)

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

print("✅ DONE")
