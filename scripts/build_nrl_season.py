import requests
import json
import sys
from pathlib import Path
from bs4 import BeautifulSoup

BASE = "https://www.rugbyleagueproject.org"

# season passed from command line or default
SEASON = int(sys.argv[1]) if len(sys.argv) > 1 else 2026

OUTPUT = Path(f"docs/data/nrl/seasons/{SEASON}.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

headers = {"User-Agent": "Mozilla/5.0"}

print(f"Building NRL season {SEASON}")

season_url = f"{BASE}/seasons/nrl-{SEASON}/results.html"

print("Downloading season results page...")

r = requests.get(season_url, headers=headers)
soup = BeautifulSoup(r.text, "html.parser")

match_links = []

for a in soup.select("a"):
    href = a.get("href","")
    if f"/seasons/nrl-{SEASON}/" in href and "round-" in href and href.endswith(".html"):
        match_links.append(BASE + href)

match_links = sorted(list(set(match_links)))

print("Matches discovered:", len(match_links))

rows = []
match_counter = 1

for url in match_links:

    print("Processing match:", url)

    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    try:
        score = soup.find("h1").text.strip()
        home_points, away_points = score.split("-")
    except:
        continue

    teams = soup.select("h2")

    if len(teams) < 2:
        continue

    home_team = teams[0].text.strip()
    away_team = teams[1].text.strip()

    venue = ""
    crowd = None
    date_iso = ""

    for p in soup.select("p"):
        txt = p.text

        if "Venue:" in txt:
            venue = txt.split("Venue:")[1].split(",")[0].strip()

        if "Crowd:" in txt:
            try:
                crowd = int(txt.split("Crowd:")[1].split(",")[0].strip())
            except:
                pass

        if "Date:" in txt:
            date_iso = txt.split("Date:")[1].split(",")[0].strip()

    tables = soup.select("table")

    for table in tables:

        team_header = table.find_previous("h3")
        if not team_header:
            continue

        played_for = team_header.text.strip()

        for tr in table.select("tr")[1:]:

            cols = [c.text.strip() for c in tr.select("td")]

            if len(cols) < 5:
                continue

            player = cols[0]

            try:
                tries = int(cols[1])
            except:
                tries = 0

            goals_made = 0
            goals_attempted = 0

            goals = cols[2]

            if "/" in goals:
                gm, ga = goals.split("/")
                try:
                    goals_made = int(gm)
                    goals_attempted = int(ga)
                except:
                    pass

            try:
                field_goals = int(cols[3])
            except:
                field_goals = 0

            try:
                points = int(cols[4])
            except:
                points = 0

            row = {
                "season": SEASON,
                "match_id": f"{SEASON}{match_counter:04}",
                "venue": venue,
                "crowd": crowd,
                "date_iso": date_iso,
                "home_team": home_team,
                "away_team": away_team,
                "home_points": int(home_points),
                "away_points": int(away_points),
                "margin": abs(int(home_points) - int(away_points)),
                "total_points": int(home_points) + int(away_points),

                "player": player,
                "played_for": played_for,

                "tries": tries,
                "goals_made": goals_made,
                "goals_attempted": goals_attempted,
                "field_goals": field_goals,
                "points": points
            }

            rows.append(row)

    match_counter += 1

print("Player rows collected:", len(rows))

with open(OUTPUT, "w") as f:
    json.dump(rows, f, indent=2)

print("Season written to:", OUTPUT)
