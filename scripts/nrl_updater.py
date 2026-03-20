import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path

print("NRL MATCH + PLAYER UPDATER (FIXED)")

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


# -----------------------------
# 🔥 GET SEASON PAGE
# -----------------------------
print("Downloading season page...")

season_html = requests.get(f"{BASE}seas/{SEASON}.html", headers=HEADERS).text
season_soup = BeautifulSoup(season_html, "html.parser")

match_links = []

# 🔥 FIX: grab ALL links that point to matches
for a in season_soup.find_all("a", href=True):

    href = a["href"]

    if "matches" in href or "match" in href:
        if not href.startswith("http"):
            href = BASE + href.replace("../", "")
        match_links.append(href)

match_links = sorted(set(match_links))

print("Match pages found:", len(match_links))

if len(match_links) == 0:
    print("🚨 NO MATCHES FOUND - PAGE STRUCTURE CHANGED")
    exit()


# -----------------------------
# 🔥 PROCESS MATCHES
# -----------------------------
games = []

for link in match_links:

    match_id = link.split("/")[-1].replace(".html", "")
    print("Processing:", match_id)

    try:
        html = requests.get(link, headers=HEADERS).text
        soup = BeautifulSoup(html, "html.parser")
    except:
        print("❌ Failed to load:", link)
        continue

    # -----------------------------
    # 🔥 HEADER
    # -----------------------------
    h2 = soup.find("h2")
    header = h2.get_text(" ", strip=True) if h2 else ""

    home_team = ""
    away_team = ""
    home_points = 0
    away_points = 0

    # 🔥 HANDLE MULTIPLE FORMATS
    if " def. " in header:
        parts = header.split(" def. ")
    elif " bt " in header:
        parts = header.split(" bt ")
    else:
        parts = []

    if len(parts) == 2:
        try:
            home_team = parts[0].rsplit(" ", 1)[0]
            home_points = int(parts[0].rsplit(" ", 1)[1])

            away_team = parts[1].rsplit(" ", 1)[0]
            away_points = int(parts[1].rsplit(" ", 1)[1])
        except:
            print("⚠️ Header parse failed:", header)

    total_points = home_points + away_points
    margin = abs(home_points - away_points)

    # -----------------------------
    # 🔥 PLAYER TABLES
    # -----------------------------
    tables = soup.find_all("table")

    if len(tables) < 2:
        print("⚠️ No player tables:", match_id)
        continue

    def extract_players(table, team_name):

        players = []

        for row in table.find_all("tr"):

            cols = row.find_all("td")

            if len(cols) < 5:
                continue

            name = cols[0].get_text(strip=True)

            if not name or name.lower() in ["totals", "team"]:
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
                "goals_attempted": 0,
                "field_goals": field_goals,
                "points": points
            })

        return players

    home_players = extract_players(tables[0], home_team)
    away_players = extract_players(tables[1], away_team)

    if not home_players and not away_players:
        print("⚠️ No players found:", match_id)
        continue

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
# 🔥 SAVE
# -----------------------------
with open(OUTPUT, "w") as f:
    json.dump(games, f, indent=2)

print("\n==============================")
print("Matches processed:", len(games))
print("Saved to:", OUTPUT)
print("==============================")
