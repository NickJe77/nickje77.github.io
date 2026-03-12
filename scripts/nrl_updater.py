import json
import requests
from pathlib import Path
from bs4 import BeautifulSoup

print("NRL AFLTABLES UPDATER")

SEASON = 2026

BASE = Path("docs/data/nrl")
MATCH_FILE = BASE / "matches" / f"{SEASON}.json"

BASE.mkdir(parents=True, exist_ok=True)
MATCH_FILE.parent.mkdir(parents=True, exist_ok=True)

URL = f"https://afltables.com/rl/seas/{SEASON}.html"

print("Downloading season page")

html = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}).text
soup = BeautifulSoup(html, "html.parser")

rows = soup.find_all("tr")

matches = []
i = 0

while i < len(rows):

    cols = rows[i].find_all("td")

    if len(cols) >= 3:

        team1 = cols[0].get_text(strip=True)
        score1 = cols[2].get_text(strip=True)

        # check if score column is numeric
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
    with open(MATCH_FILE) as f:
        existing = json.load(f)

existing_keys = {(m["home_team"], m["away_team"]) for m in existing}

rows_out = existing.copy()
added = 0

for m in matches:

    key = (m["home_team"], m["away_team"])

    if key in existing_keys:
        continue

    rows_out.append(m)
    added += 1
    print("Added", m["home_team"], "vs", m["away_team"])

with open(MATCH_FILE, "w") as f:
    json.dump(rows_out, f, indent=2)

print("Matches added:", added)
print("Updater complete")
