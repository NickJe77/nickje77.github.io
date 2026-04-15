import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re

print("ALL-NBA BUILDER (FINAL FIX)")

URL = "https://www.nba.com/news/history-all-nba-teams"

OUTPUT = Path("docs/data/nba/all_nba.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0"
}

res = requests.get(URL, headers=headers)
html = res.text

# 🔥 Extract embedded JSON from page
match = re.search(r'window\.__NUXT__=(.*?);\s*</script>', html)

if not match:
    print("❌ Could not find embedded data")
    exit()

nuxt_data = json.loads(match.group(1))

# 🔥 Navigate to article body
body = nuxt_data["data"][0]["content"]["body"]

data = []

TEAM_MAP = {
    "Bucks":"MIL","Thunder":"OKC","Nuggets":"DEN","Cavaliers":"CLE","Celtics":"BOS",
    "Knicks":"NYK","Warriors":"GSW","Timberwolves":"MIN","Lakers":"LAL","Pistons":"DET",
    "Pacers":"IND","Clippers":"LAC","Mavericks":"DAL","Suns":"PHX","76ers":"PHI",
    "Heat":"MIA","Kings":"SAC","Trail Blazers":"POR","Raptors":"TOR","Bulls":"CHI",
    "Nets":"BKN","Hawks":"ATL","Jazz":"UTA","Wizards":"WAS","Pelicans":"NOP",
    "Hornets":"CHA","Grizzlies":"MEM","Spurs":"SAS","Rockets":"HOU","Magic":"ORL"
}

def abbr(team):
    return TEAM_MAP.get(team, team)

current = None

for block in body:

    # season header
    if block.get("type") == "heading":
        text = block.get("text", "")
        if re.match(r"\d{4}-\d{2}", text):
            if current:
                data.append(current)

            current = {
                "season": text,
                "first_team": [],
                "second_team": [],
                "third_team": []
            }
            continue

    # paragraphs (contain teams)
    if block.get("type") == "paragraph" and current:
        text = block.get("text", "")

        if "First Team" in text:
            key = "first_team"
        elif "Second Team" in text:
            key = "second_team"
        elif "Third Team" in text:
            key = "third_team"
        else:
            continue

        players = text.split(":")[-1].split(";")

        for p in players:
            if "," in p:
                name, team = p.split(",", 1)

                current[key].append({
                    "player": name.strip(),
                    "team": abbr(team.strip())
                })

# append last
if current:
    data.append(current)

with open(OUTPUT, "w") as f:
    json.dump(data, f, indent=2)

print(f"✅ DONE: {len(data)} seasons saved")
