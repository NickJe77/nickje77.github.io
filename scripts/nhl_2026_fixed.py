import requests
import json
from pathlib import Path

print("NHL 2026 BUILDER (FIXED - TEAM METHOD)")

OUTPUT = Path("docs/data/nhl/seasons/2026.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

SEASON = "20252026"

# ALL NHL TEAMS
TEAMS = [
    "ANA","ARI","BOS","BUF","CGY","CAR","CHI","COL","CBJ","DAL",
    "DET","EDM","FLA","LAK","MIN","MTL","NSH","NJD","NYI","NYR",
    "OTT","PHI","PIT","SEA","SJS","STL","TBL","TOR","VAN","VGK",
    "WSH","WPG"
]

games = {}
    
for team in TEAMS:
    print(f"Fetching {team}")

    url = f"https://api-web.nhle.com/v1/club-schedule-season/{team}/{SEASON}"

    try:
        data = requests.get(url).json()
    except:
        continue

    for game in data.get("games", []):

        game_id = game.get("id")
        game_type = game.get("gameType")

        if game_type not in [2, 3]:
            continue

        # dedupe
        if game_id in games:
            continue

        home = game.get("homeTeam", {})
        away = game.get("awayTeam", {})

        games[game_id] = {
            "game_id": game_id,
            "date": game.get("gameDate"),
            "home_team": home.get("abbrev"),
            "away_team": away.get("abbrev"),
            "home_score": home.get("score"),
            "away_score": away.get("score"),
            "venue": game.get("venue", {}).get("default")
        }

print(f"Total games: {len(games)}")

# SAVE
OUTPUT.write_text(json.dumps(list(games.values()), indent=2))

print("Saved 2026.json")
