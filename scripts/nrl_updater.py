import json
import requests
from pathlib import Path
from bs4 import BeautifulSoup

print("NRL FULL UPDATER")

SEASON = 2026

BASE = Path("docs/data/nrl")
MATCH_FILE = BASE / "matches" / f"{SEASON}.json"

BASE.mkdir(parents=True, exist_ok=True)
MATCH_FILE.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}


def get_match_ids():

    url = f"https://www.rugbyleagueproject.org/seasons/nrl-{SEASON}/results.html"

    r = requests.get(url, headers=HEADERS)

    soup = BeautifulSoup(r.text,"html.parser")

    ids = []

    for a in soup.select("a[href*='/matches/']"):
        href = a.get("href")
        mid = href.split("/")[-1].replace(".html","")
        ids.append(mid)

    return sorted(list(set(ids)))


print("Discovering matches")

match_ids = get_match_ids()

print("Matches detected:", len(match_ids))


existing = []

if MATCH_FILE.exists():
    with open(MATCH_FILE) as f:
        existing = json.load(f)

existing_ids = {m["match_id"] for m in existing}

print("Existing matches:", len(existing_ids))


def scrape_match(match_id):

    url = f"https://www.rugbyleagueproject.org/matches/{match_id}.html"

    r = requests.get(url, headers=HEADERS)

    soup = BeautifulSoup(r.text,"html.parser")

    players = []

    for li in soup.select("li"):

        text = li.text.strip()

        if "(" not in text:
            continue

        name = text.split("(")[0].strip()

        try:

            tries = text.count("try")

            goals = text.count("goal")

            players.append({
                "player": name,
                "tries": tries,
                "goals_made": goals,
                "goals_attempted": goals,
                "field_goals": 0,
                "points": tries*4 + goals*2
            })

        except:
            continue

    if not players:
        return None

    return {
        "season": SEASON,
        "match_id": match_id,
        "players": players
    }


rows = existing.copy()

added = 0

for match_id in match_ids:

    if match_id in existing_ids:
        continue

    data = scrape_match(match_id)

    if not data:
        continue

    rows.append(data)

    added += 1

    print("Added match", match_id)


if added == 0:

    print("No new matches found")

else:

    with open(MATCH_FILE,"w") as f:
        json.dump(rows,f,indent=2)

    print("Matches added:", added)


print("Updater complete")
