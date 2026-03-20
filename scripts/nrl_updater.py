import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path

print("NRL MATCH + PLAYER UPDATER (FINAL LOCKED VERSION)")

SEASON = 2026
BASE = "https://afltables.com/rl/"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# 🔥 WRITE TO NEW FILE (CANNOT BE OVERWRITTEN)
ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "docs/data/nrl/matches" / f"{SEASON}_NEW.json"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

print("Saving to:", OUTPUT.resolve())


def safe_int(x):
    try:
        return int(x.strip())
    except:
        return 0


# -----------------------------
# GET SEASON PAGE
# -----------------------------
print("Downloading season page...")
season_html = requests.get(f"{BASE}seas/{SEASON}.html", headers=HEADERS).text
soup = BeautifulSoup(season_html, "html.parser")

# -----------------------------
# GET MATCH LINKS (CORRECT)
# -----------------------------
match_links = []

for a in soup.find_all("a", href=True):
    href = a["href"]

    if "matches/" in href and href.endswith(".html"):
        if not href.startswith("http"):
            href = BASE + href.replace("../", "")
        match_links.append(href)

match_links = sorted(set(match_links))

print("Match pages found:", len(match_links))

if not match_links:
    print("🚨 NO MATCH LINKS FOUND — STOPPING")
    exit()


# -----------------------------
# PROCESS MATCHES
# -----------------------------
games = []

for link in match_links:

    match_id = link.split("/")[-1].replace(".html", "")
    print("Processing:", match_id)

    try:
        html = requests.get(link, headers=HEADERS).text
        soup = BeautifulSoup(html, "html.parser")
    except:
        print("❌ Failed:", link)
        continue

    # -----------------------------
    # HEADER
    # -----------------------------
    h2 = soup.find("h2")
    header = h2.get_text(" ", strip=True) if h2 else ""

    home_team = ""
    away_team = ""
    home_points = 0
    away_points = 0

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
            print("⚠️ Header fail:", header)

    total_points = home_points + away_points
    margin = abs(home_points - away_points)

    # -----------------------------
    # PLAYER TABLES
    # -----------------------------
    tables = soup.find_all("table")

    if len(tables) < 2:
        print("⚠️ No tables:", match_id)
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

            players.append({
                "player": name,
                "played_for": team_name,
                "tries": safe_int(cols[1].text),
                "goals_made": safe_int(cols[2].text),
                "goals_attempted": 0,
                "field_goals": safe_int(cols[3].text),
                "points": safe_int(cols[4].text)
            })

        return players

    home_players = extract_players(tables[0], home_team)
    away_players = extract_players(tables[1], away_team)

    players = home_players + away_players

    if not players:
        print("⚠️ No players:", match_id)
        continue

    game = {
        "season": SEASON,
        "match_id": match_id,
        "home_team": home_team,
        "away_team": away_team,
        "home_points": home_points,
        "away_points": away_points,
        "total_points": total_points,
        "margin": margin,
        "players": players
    }

    # 🔥 DEBUG — SHOW FIRST GAME STRUCTURE
    if len(games) == 0:
        print("\nSAMPLE GAME STRUCTURE:")
        print(json.dumps(game, indent=2))

    games.append(game)


# -----------------------------
# SAVE FILE
# -----------------------------
with open(OUTPUT, "w") as f:
    json.dump(games, f, indent=2)

print("\n==============================")
print("Games saved:", len(games))
print("File:", OUTPUT)
print("==============================")
