import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path

BASE = "https://www.rugbyleagueproject.org"
URL = "https://www.rugbyleagueproject.org/seasons/nrl-2026/results.html"

FILE = Path("docs/data/nrl/matches/2026.json")

print("Downloading RugbyLeagueProject results page")

html = requests.get(URL).text
soup = BeautifulSoup(html, "html.parser")

rows = []

table = soup.find("table")

trs = table.find_all("tr")

for tr in trs:

    tds = tr.find_all("td")

    if len(tds) < 5:
        continue

    date = tds[0].text.strip()
    home = tds[1].text.strip()
    score = tds[2].text.strip()
    away = tds[3].text.strip()
    venue = tds[4].text.strip()

    if "-" not in score:
        continue

    home_points, away_points = score.split("-")

    row = {
        "season": 2026,
        "match_id": f"{date}-{home}-{away}",
        "date_iso": "",
        "venue": venue,
        "home_team": home,
        "away_team": away,
        "home_points": int(home_points),
        "away_points": int(away_points),
        "margin": abs(int(home_points) - int(away_points)),
        "total_points": int(home_points) + int(away_points),
        "player": "",
        "played_for": "",
        "tries": 0,
        "goals_made": 0,
        "goals_attempted": 0,
        "field_goals": 0,
        "points": 0
    }

    rows.append(row)

print("Matches collected:", len(rows))

FILE.parent.mkdir(parents=True, exist_ok=True)

with open(FILE, "w") as f:
    json.dump(rows, f, indent=2)

print("2026 season rebuilt successfully")
