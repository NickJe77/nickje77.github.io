import json
import requests
from pathlib import Path
from bs4 import BeautifulSoup

print("NRL FULL PLAYER STATS UPDATER")

SEASON = 2026

BASE = Path("docs/data/nrl")
MATCH_FILE = BASE / "matches" / f"{SEASON}.json"

BASE.mkdir(parents=True, exist_ok=True)
MATCH_FILE.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

url = f"https://afltables.com/rl/seas/{SEASON}.html"

print("Downloading AFLTables season page")

html = requests.get(url, headers=HEADERS).text
soup = BeautifulSoup(html, "html.parser")

rows = soup.find_all("tr")

matches = []
i = 0

while i < len(rows):

    cols = rows[i].find_all("td")

    if len(cols) >= 3:

        team1 = cols[0].get_text(strip=True)
        score1 = cols[2].get_text(strip=True)

        if score1.isdigit():

            cols2 = rows[i+1].find_all("td")

            if len(cols2) >= 3:

                team2 = cols2[0].get_text(strip=True)
                score2 = cols2[2].get_text(strip=True)

                if score2.isdigit():

                    matches.append({
                        "season": SEASON,
                        "home_team": team1,
                        "away_team": team2,
                        "home_score": int(score1),
                        "away_score": int(score2)
                    })

                    i += 2
                    continue

    i += 1

print("Matches detected:", len(matches))

existing = []

if MATCH_FILE.exists():
    try:
        with open(MATCH_FILE) as f:
            existing = json.load(f)
    except:
        existing = []

updated = 0

for m in matches:

    found = False

    for e in existing:

        if (
            e.get("home_team") == m["home_team"]
            and e.get("away_team") == m["away_team"]
        ):
            e.update(m)
            found = True
            updated += 1
            break

    if not found:
        existing.append(m)
        updated += 1

with open(MATCH_FILE, "w") as f:
    json.dump(existing, f, indent=2, sort_keys=True)

print("Matches updated:", updated)
print("Updater complete")
