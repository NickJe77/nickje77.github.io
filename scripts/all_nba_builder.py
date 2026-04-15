import requests
from bs4 import BeautifulSoup, Comment
import json
from pathlib import Path

print("ALL-NBA BUILDER (FINAL WORKING - COMMENTS FIX)")

URL = "https://www.basketball-reference.com/awards/all_nba.html"

OUTPUT = Path("docs/data/nba/all_nba.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

headers = {"User-Agent": "Mozilla/5.0"}
res = requests.get(URL, headers=headers)
soup = BeautifulSoup(res.text, "html.parser")

# 🔥 FIND TABLE INSIDE COMMENTS
comments = soup.find_all(string=lambda text: isinstance(text, Comment))

table = None

for c in comments:
    if "id=\"all_nba\"" in c:
        comment_soup = BeautifulSoup(c, "html.parser")
        table = comment_soup.find("table", {"id": "all_nba"})
        break

if not table:
    print("❌ Table not found")
    exit()

tbody = table.find("tbody")

data = []
season_obj = None
current_season = None

TEAM_MAP = {
    "BRK": "BKN",
    "CHO": "CHA"
}

for row in tbody.find_all("tr"):

    if row.get("class") and "thead" in row.get("class"):
        continue

    season = row.find("th").text.strip()
    tds = row.find_all("td")

    if not tds:
        continue

    team_type = tds[0].text.strip()

    if season != current_season:
        if season_obj:
            data.append(season_obj)

        season_obj = {
            "season": season,
            "first_team": [],
            "second_team": [],
            "third_team": []
        }
        current_season = season

    key = None
    if team_type == "1st":
        key = "first_team"
    elif team_type == "2nd":
        key = "second_team"
    elif team_type == "3rd":
        key = "third_team"

    if not key:
        continue

    players = tds[1:6]
    teams = tds[6:11]

    for p, t in zip(players, teams):
        name = p.text.strip()
        team = t.text.strip()

        if name:
            team = TEAM_MAP.get(team, team)

            season_obj[key].append({
                "player": name,
                "team": team
            })

# append last
if season_obj:
    data.append(season_obj)

with open(OUTPUT, "w") as f:
    json.dump(data, f, indent=2)

print(f"✅ DONE: {len(data)} seasons saved")
