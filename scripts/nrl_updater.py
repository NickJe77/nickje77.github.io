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

HEADERS = {"User-Agent": "Mozilla/5.0"}

print("Downloading season page")

html = requests.get(URL, headers=HEADERS).text

soup = BeautifulSoup(html, "html.parser")

tables = soup.find_all("table")

matches = []

for table in tables:

    rows = table.find_all("tr")

    for r in rows:

        cols = [c.get_text(strip=True) for c in r.find_all("td")]

        if len(cols) < 4:
            continue

        team1 = cols[0]
        score1 = cols[1]
        team2 = cols[2]
        score2 = cols[3]

        if not score1.isdigit() or not score2.isdigit():
            continue

        matches.append({
            "season": SEASON,
            "home_team": team1,
            "home_score": int(score1),
            "away_team": team2,
            "away_score": int(score2)
        })

print("Matches detected:", len(matches))


existing = []

if MATCH_FILE.exists():
    try:
        with open(MATCH_FILE) as f:
            existing = json.load(f)
    except:
        existing = []


existing_set = {
    (m["home_team"], m["away_team"], m["home_score"], m["away_score"])
    for m in existing
}

rows = existing.copy()
added = 0


for m in matches:

    key = (m["home_team"], m["away_team"], m["home_score"], m["away_score"])

    if key in existing_set:
        continue

    rows.append(m)

    added += 1

    print("Added", m["home_team"], "vs", m["away_team"])


with open(MATCH_FILE, "w") as f:
    json.dump(rows, f, indent=2)


print("Matches added:", added)
print("Updater complete")
