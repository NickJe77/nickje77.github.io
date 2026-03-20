import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path

print("NRL CLEAN PLAYER + MATCH UPDATER")

SEASON = 2026
BASE = "https://afltables.com/rl/"
HEADERS = {"User-Agent": "Mozilla/5.0"}

OUTPUT = Path(f"docs/data/nrl/{SEASON}.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

def safe_int(x):
    try:
        return int(x.strip())
    except:
        return 0


print("Downloading season page")

season_html = requests.get(f"{BASE}seas/{SEASON}.html", headers=HEADERS).text
season_soup = BeautifulSoup(season_html, "html.parser")

match_links = []

for a in season_soup.find_all("a", href=True):
    if a.text.strip() == "Match details":
        href = a["href"]
        if not href.startswith("http"):
            href = BASE + href.replace("../","")
        match_links.append(href)

match_links = sorted(set(match_links))
print("Match pages found:", len(match_links))


games = []

for link in match_links:

    match_id = link.split("/")[-1].replace(".html","")
    print("Processing", match_id)

    html = requests.get(link, headers=HEADERS).text
    soup = BeautifulSoup(html, "html.parser")

    # 🔥 GET TEAMS
    h2 = soup.find("h2")
    teams_text = h2.get_text(" ", strip=True) if h2 else ""

    # Example: "Melbourne Storm 24 def. Sydney Roosters 18"
    parts = teams_text.split(" def. ")

    home_team = parts[0].rsplit(" ",1)[0] if len(parts) > 1 else ""
    away_team = parts[1].rsplit(" ",1)[0] if len(parts) > 1 else ""

    # 🔥 GET SCORES
    try:
        home_score = int(parts[0].rsplit(" ",1)[1])
        away_score = int(parts[1].rsplit(" ",1)[1])
    except:
        home_score = 0
        away_score = 0

    tables = soup.find_all("table")

    if len(tables) < 2:
        continue

    def extract_players(table):

        players = []

        for row in table.find_all("tr"):

            cols = row.find_all("td")

            if len(cols) < 5:
                continue

            name = cols[0].get_text(strip=True)

            # 🔥 skip junk rows
            if not name or name.lower() in ["totals","team"]:
                continue

            tries = safe_int(cols[1].text)
            goals = safe_int(cols[2].text)
            fg = safe_int(cols[3].text)
            pts = safe_int(cols[4].text)

            players.append({
                "player": name,
                "tries": tries,
                "goals": goals,
                "field_goals": fg,
                "points": pts
            })

        return players

    # 🔥 FIRST TWO TABLES = TEAMS
    home_players = extract_players(tables[0])
    away_players = extract_players(tables[1])

    games.append({
        "match_id": match_id,
        "season": SEASON,

        "home_team": home_team,
        "away_team": away_team,

        "home_score": home_score,
        "away_score": away_score,

        "home_players": home_players,
        "away_players": away_players
    })


with open(OUTPUT, "w") as f:
    json.dump(games, f, indent=2)

print("Matches processed:", len(games))
print("Updater complete")
