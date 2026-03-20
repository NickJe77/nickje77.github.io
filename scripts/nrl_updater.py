import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path

print("NRL MATCH + PLAYER UPDATER (CORRECT STRUCTURE)")

SEASON = 2026
BASE = "https://afltables.com/rl/"
HEADERS = {"User-Agent": "Mozilla/5.0"}

OUTPUT = Path(f"docs/data/nrl/matches/{SEASON}.json")
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

    # -----------------------------
    # 🔥 GET MATCH HEADER
    # -----------------------------
    h2 = soup.find("h2")
    header = h2.get_text(" ", strip=True) if h2 else ""

    # Example:
    # "Canberra 30 def. New Zealand 8"

    parts = header.split(" def. ")

    home_team = ""
    away_team = ""
    home_points = 0
    away_points = 0

    if len(parts) == 2:
        try:
            home_team = parts[0].rsplit(" ",1)[0]
            home_points = int(parts[0].rsplit(" ",1)[1])

            away_team = parts[1].rsplit(" ",1)[0]
            away_points = int(parts[1].rsplit(" ",1)[1])
        except:
            pass

    total_points = home_points + away_points
    margin = abs(home_points - away_points)

    # -----------------------------
    # 🔥 PLAYER TABLES
    # -----------------------------
    tables = soup.find_all("table")

    if len(tables) < 2:
        continue

    def extract_players(table, team_name):

        players = []

        for row in table.find_all("tr"):

            cols = row.find_all("td")

            if len(cols) < 5:
                continue

            name = cols[0].get_text(strip=True)

            # skip junk rows
            if not name or name.lower() in ["totals","team"]:
                continue

            tries = safe_int(cols[1].text)
            goals_made = safe_int(cols[2].text)
            field_goals = safe_int(cols[3].text)
            points = safe_int(cols[4].text)

            players.append({
                "player": name,
                "played_for": team_name,
                "tries": tries,
                "goals_made": goals_made,
                "goals_attempted": 0,  # not available on site
                "field_goals": field_goals,
                "points": points
            })

        return players

    home_players = extract_players(tables[0], home_team)
    away_players = extract_players(tables[1], away_team)

    # 🔥 MERGE INTO ONE LIST (YOUR STRUCTURE)
    players = home_players + away_players

    games.append({
        "season": SEASON,
        "match_id": match_id,

        "home_team": home_team,
        "away_team": away_team,

        "home_points": home_points,
        "away_points": away_points,
        "total_points": total_points,
        "margin": margin,

        "players": players
    })


# -----------------------------
# 🔥 SAVE FILE
# -----------------------------
with open(OUTPUT, "w") as f:
    json.dump(games, f, indent=2)

print("Matches processed:", len(games))
print("Saved to:", OUTPUT)
print("Updater complete")
