import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path

SEASON = "nrl-2026"

RESULTS_URL = f"https://www.rugbyleagueproject.org/seasons/{SEASON}/results.html"

FILE = Path("docs/data/nrl/matches/2026.json")

print("Downloading RugbyLeagueProject results page")

html = requests.get(RESULTS_URL).text

soup = BeautifulSoup(html, "html.parser")

links = soup.find_all("a")

match_links = []

for link in links:

    href = link.get("href")

    if not href:
        continue

    if f"/seasons/{SEASON}/" not in href:
        continue

    if "summary.html" not in href:
        continue

    match_links.append("https://www.rugbyleagueproject.org" + href)

print("Matches found:", len(match_links))

with open(FILE) as f:
    rows = json.load(f)

existing = {r["match_id"] for r in rows}

added = 0

for url in match_links:

    match_id = url.split("/")[-2]

    if match_id in existing:
        continue

    page = requests.get(url).text

    soup = BeautifulSoup(page, "html.parser")

    title = soup.find("title").text

    teams = title.split(" v ")

    home_team = teams[0].strip()
    away_team = teams[1].split("-")[0].strip()

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
