import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path

URL = "https://www.rugbyleagueproject.org/seasons/nrl-2026/results.html"

OUT = Path("docs/data/nrl/matches/2026.json")

print("Downloading RugbyLeagueProject results page")

html = requests.get(URL).text
soup = BeautifulSoup(html, "html.parser")

rows = []

tables = soup.find_all("table")

for table in tables:

    trs = table.find_all("tr")

    for tr in trs:

        cols = [c.text.strip() for c in tr.find_all("td")]

        if len(cols) < 5:
            continue

        date = cols[0]
        home = cols[1]
        score = cols[2]
        away = cols[3]
        venue = cols[4]

        if "-" not in score:
            continue

        try:
            h, a = score.split("-")
            h = int(h)
            a = int(a)
        except:
            continue

        rows.append({
            "season": 2026,
            "match_id": f"{date}-{home}-{away}",
            "date_iso": "",
            "venue": venue,
            "home_team": home,
            "away_team": away,
            "home_points": h,
            "away_points": a,
            "margin": abs(h-a),
            "total_points": h+a,
            "player": "",
            "played_for": "",
            "tries": 0,
            "goals_made": 0,
            "goals_attempted": 0,
            "field_goals": 0,
            "points": 0
        })

print("Matches collected:", len(rows))

OUT.parent.mkdir(parents=True, exist_ok=True)

with open(OUT, "w") as f:
    json.dump(rows, f, indent=2)

print("2026 season rebuilt successfully")
