import requests
from bs4 import BeautifulSoup, Comment
import json
import re

print("BUILDING FULL ALL-NBA DATASET")

URL = "https://www.basketball-reference.com/awards/all_nba.html"

headers = {
    "User-Agent": "Mozilla/5.0"
}

res = requests.get(URL, headers=headers)
soup = BeautifulSoup(res.text, "html.parser")

# extract table from comments (works locally)
comments = soup.find_all(string=lambda text: isinstance(text, Comment))

table = None
for c in comments:
    if "all_nba" in c:
        table = BeautifulSoup(c, "html.parser").find("table")
        break

if not table:
    raise Exception("Table not found")

rows = table.find("tbody").find_all("tr")

data = []
current_season = None
season_obj = None

TEAM_MAP = {
    "BRK":"BKN",
    "CHO":"CHA"
}

for row in rows:
    if "class" in row.attrs and "thead" in row.attrs["class"]:
        continue

    season = row.find("th").text.strip()
    cols = row.find_all("td")

    if not cols:
        continue

    team_type = cols[0].text.strip()

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

    players = cols[1:6]
    teams = cols[6:11]

    for p, t in zip(players, teams):
        name = p.text.strip()
        team = t.text.strip()

        if name:
            team = TEAM_MAP.get(team, team)

            season_obj[key].append({
                "player": name,
                "team": team
            })

if season_obj:
    data.append(season_obj)

# reverse so newest first (matches your site style)
data = list(reversed(data))

with open("all_nba_full.json", "w") as f:
    json.dump(data, f, indent=2)

print(f"✅ DONE: {len(data)} seasons built")
