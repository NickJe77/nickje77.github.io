import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path

BASE = "https://www.rugbyleagueproject.org"
RESULTS = "https://www.rugbyleagueproject.org/seasons/nrl-2026/results.html"

FILE = Path("docs/data/nrl/matches/2026.json")

print("Downloading RugbyLeagueProject results page")

html = requests.get(RESULTS).text
soup = BeautifulSoup(html, "html.parser")

links = soup.find_all("a")

rows = []

for link in links:

    href = link.get("href")

    if not href:
        continue

    if "/seasons/nrl-2026/" not in href:
        continue

    if not href.endswith("summary.html"):
        continue

    url = BASE + href

    page = requests.get(url).text
    match = BeautifulSoup(page, "html.parser")

    title = match.find("title").text

    try:
        teams = title.split(" v ")
        home_team = teams[0].strip()
        away_team = teams[1].split("-")[0].strip()
    except:
        continue

    score_tag = match.find("h2")

    if score_tag:
        score = score_tag.text.strip()
    else:
        score = "0-0"

    try:
        home_points, away_points = score.split("-")
    except:
        home_points = 0
        away_points = 0

    venue = ""

    meta = match.find_all("li")

    for m in meta:
        if "Venue" in m.text:
            venue = m.text.replace("Venue:", "").strip()

    match_id = href.replace("/summary.html","").replace("/seasons/","")

    row = {
        "season": 2026,
        "match_id": match_id,
        "date_iso": "",
        "venue": venue,
        "home_team": home_team,
        "away_team": away_team,
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

with open(FILE, "w") as f:
    json.dump(rows, f, indent=2)

print("2026 season rebuilt successfully")
