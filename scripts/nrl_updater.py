import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path

print("NRL FULL UPDATER")

SEASON = 2026

BASE = Path("docs/data/nrl")
MATCH_FILE = BASE / "matches" / f"{SEASON}.json"

BASE.mkdir(parents=True, exist_ok=True)
MATCH_FILE.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}


def get_season_matches():

    url = f"https://www.rugbyleagueproject.org/seasons/nrl-{SEASON}/results.html"

    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:
        print("Failed to load season page")
        return []

    soup = BeautifulSoup(r.text, "html.parser")

    matches = []

    for a in soup.select("a[href*='/matches/']"):

        href = a.get("href")

        if "/matches/" not in href:
            continue

        match_id = href.split("/")[-1].replace(".html","")

        matches.append(match_id)

    return list(set(matches))


print("Discovering matches")

match_ids = get_season_matches()

print("Matches detected:", len(match_ids))


existing = []

if MATCH_FILE.exists():

    with open(MATCH_FILE) as f:
        existing = json.load(f)

existing_ids = {m["match_id"] for m in existing}

print("Existing matches:", len(existing_ids))


rows = existing.copy()

added = 0


def get_match(match_id):

    url = f"https://www.rugbyleagueproject.org/matches/{match_id}.html"

    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:
        return None

    soup = BeautifulSoup(r.text,"html.parser")

    teams = soup.select(".team")

    if len(teams) < 2:
        return None

    home = teams[0].text.strip()
    away = teams[1].text.strip()

    players = []

    for row in soup.select("table.players tr"):

        cols = [c.text.strip() for c in row.select("td")]

        if len(cols) < 6:
            continue

        players.append({
            "player": cols[0],
            "played_for": cols[1],
            "tries": int(cols[2] or 0),
            "goals_made": int(cols[3] or 0),
            "goals_attempted": int(cols[4] or 0),
            "field_goals": int(cols[5] or 0),
            "points": int(cols[6] or 0)
        })

    if not players:
        return None

    return {
        "season": SEASON,
        "match_id": match_id,
        "home_team": home,
        "away_team": away,
        "players": players
    }


for match_id in match_ids:

    if match_id in existing_ids:
        continue

    data = get_match(match_id)

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
