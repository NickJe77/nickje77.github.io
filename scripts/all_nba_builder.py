import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re

print("ALL-NBA BUILDER (FIXED PARSER)")

URL = "https://www.nba.com/news/history-all-nba-teams"

OUTPUT = Path("docs/data/nba/all_nba.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0"
}

res = requests.get(URL, headers=headers)
soup = BeautifulSoup(res.text, "html.parser")

# 🔥 KEY FIX: target article content only
article = soup.find("article")

if not article:
    print("❌ Could not find article content")
    exit()

text = article.get_text("\n")

lines = [l.strip() for l in text.split("\n") if l.strip()]

data = []
season_obj = None
current_team = None

TEAM_MAP = {
    "Milwaukee Bucks":"MIL","Oklahoma City Thunder":"OKC","Denver Nuggets":"DEN",
    "Cleveland Cavaliers":"CLE","Boston Celtics":"BOS","New York Knicks":"NYK",
    "Golden State Warriors":"GSW","Minnesota Timberwolves":"MIN",
    "Los Angeles Lakers":"LAL","Detroit Pistons":"DET","Indiana Pacers":"IND",
    "LA Clippers":"LAC","Dallas Mavericks":"DAL","Phoenix Suns":"PHX",
    "Philadelphia 76ers":"PHI","Miami Heat":"MIA","Sacramento Kings":"SAC",
    "Portland Trail Blazers":"POR","Toronto Raptors":"TOR","Chicago Bulls":"CHI",
    "Brooklyn Nets":"BKN","Atlanta Hawks":"ATL","Utah Jazz":"UTA",
    "Washington Wizards":"WAS","New Orleans Pelicans":"NOP",
    "Charlotte Hornets":"CHA","Memphis Grizzlies":"MEM",
    "San Antonio Spurs":"SAS","Houston Rockets":"HOU","Orlando Magic":"ORL"
}

def abbr(team):
    return TEAM_MAP.get(team, team)

for line in lines:

    # season
    if re.match(r"^\d{4}-\d{2}$", line):
        if season_obj:
            data.append(season_obj)

        season_obj = {
            "season": line,
            "first_team": [],
            "second_team": [],
            "third_team": []
        }
        current_team = None
        continue

    # team headers
    if "First Team" in line:
        current_team = "first_team"
        continue
    if "Second Team" in line:
        current_team = "second_team"
        continue
    if "Third Team" in line:
        current_team = "third_team"
        continue

    # players
    if current_team and season_obj:
        # expected format: Player Name, Team
        if "," in line and not any(x in line for x in ["Team", "Season"]):

            parts = line.split(",")

            if len(parts) >= 2:
                player = parts[0].strip()
                team = parts[1].strip()

                # ignore junk lines
                if len(player.split()) >= 2:
                    season_obj[current_team].append({
                        "player": player,
                        "team": abbr(team)
                    })

# append last
if season_obj:
    data.append(season_obj)

with open(OUTPUT, "w") as f:
    json.dump(data, f, indent=2)

print(f"✅ DONE: {len(data)} seasons saved")
