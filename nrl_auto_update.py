import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path

BASE = "https://www.rugbyleagueproject.org"
RESULTS = "https://www.rugbyleagueproject.org/seasons/nrl-2026/results.html"

FILE = Path("docs/data/nrl/matches/2026.json")

print("Downloading RugbyLeagueProject results page")

res = requests.get(RESULTS)
soup = BeautifulSoup(res.text, "html.parser")

links = soup.find_all("a")

match_links = []

for a in links:

    href = a.get("href")

    if not href:
        continue

    if "/seasons/nrl-2026/" not in href:
        continue

    if not href.endswith("summary.html"):
        continue

    url = BASE + href

    match_links.append(url)

print("Matches found:", len(match_links))

if FILE.exists():

    with open(FILE) as f:
        rows = json.load(f)

else:

    rows = []

existing = {r["match_id"] for r in rows if "match_id" in r}

added = 0

for url in match_links:

    match_id = url.replace(BASE + "/", "").replace("/summary.html","")

    if match_id in existing:
        continue

    page = requests.get(url)

    soup = BeautifulSoup(page.text, "html.parser")

    title = soup.find("title").text

    try:
        teams = title.split(" v ")

        home_team = teams[0].strip()
        away_team = teams[1].split("-")[0].strip()

    except:

        continue

    score_tag = soup.find("h2")

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

    meta = soup.find_all("li")

    for m in meta:

        if "Venue" in m.text:

            venue = m.text.replace("Venue:", "").strip()

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

    added += 1

with open(FILE, "w") as f:

    json.dump(rows, f, indent=2)

print("Matches added:", added)
