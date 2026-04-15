import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path

print("ALL-NBA BUILDER (WORKING HTML PARSER)")

URL = "https://www.nba.com/news/history-all-nba-teams"

OUTPUT = Path("docs/data/nba/all_nba.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

headers = {"User-Agent": "Mozilla/5.0"}
res = requests.get(URL, headers=headers)
soup = BeautifulSoup(res.text, "html.parser")

data = []

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

article = soup.find("article")

if not article:
    print("❌ Article not found")
    exit()

elements = article.find_all(["h2", "h3", "ul"])

current = None
current_team = None

for el in elements:

    # SEASON (e.g. > 2024-25)
    if el.name == "h2":
        season = el.text.replace(">", "").strip()

        if "-" in season:
            if current:
                data.append(current)

            current = {
                "season": season,
                "first_team": [],
                "second_team": [],
                "third_team": []
            }
            current_team = None

    # TEAM HEADINGS
    elif el.name == "h3" and current:
        text = el.text.strip().upper()

        if "FIRST TEAM" in text:
            current_team = "first_team"
        elif "SECOND TEAM" in text:
            current_team = "second_team"
        elif "THIRD TEAM" in text:
            current_team = "third_team"

    # PLAYER LISTS
    elif el.name == "ul" and current and current_team:
        for li in el.find_all("li"):
            text = li.text.strip()

            if "," in text:
                name, team = text.split(",", 1)

                current[current_team].append({
                    "player": name.strip(),
                    "team": abbr(team.strip())
                })

# append last season
if current:
    data.append(current)

with open(OUTPUT, "w") as f:
    json.dump(data, f, indent=2)

print(f"✅ DONE: {len(data)} seasons saved")
