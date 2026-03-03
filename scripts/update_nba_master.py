import json
import requests
import time
from pathlib import Path
from datetime import date, timedelta

# =========================
# CONFIG
# =========================

SEASON = 2025
START_DATE = date(2025, 2, 15)

OUT_DIR = Path("docs/data/nba/2025")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ✅ CORRECT historical scoreboard endpoint
SCOREBOARD_URL = "https://cdn.nba.com/static/json/liveData/scoreboard/scoreboard_{date}.json"
BOXSCORE_URL = "https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{gameId}.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# =========================
# HELPERS
# =========================

def get_json(url):
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.json()


def filename_from_gameid(game_id):
    return f"{game_id}.json"


def build_game(box):
    game = box["game"]

    home = game["homeTeam"]
    away = game["awayTeam"]

    players = []

    for team in [home, away]:
        team_name = team["teamName"]

        for p in team.get("players", []):
            stats = p.get("statistics", {})

            players.append({
                "player_id": p.get("personId"),
                "player_name": p.get("name"),
                "team": team_name,
                "minutes": stats.get("minutes"),
                "points": stats.get("points"),
                "rebounds": stats.get("reboundsTotal"),
                "assists": stats.get("assists"),
                "steals": stats.get("steals"),
                "blocks": stats.get("blocks"),
                "turnovers": stats.get("turnovers"),
                "fouls": stats.get("foulsPersonal")
            })

    return {
        "game_id": game["gameId"],
        "season": SEASON,
        "date": game["gameDate"],
        "home_team": home["teamName"],
        "away_team": away["teamName"],
        "home_score": home["score"],
        "away_score": away["score"],
        "winner": home["teamName"] if int(home["score"]) > int(away["score"]) else away["teamName"],
        "game_type": game.get("gameStatusText"),
        "arena": {
            "arenaName": game.get("arena", {}).get("arenaName"),
            "arenaCity": game.get("arena", {}).get("arenaCity"),
            "arenaState": game.get("arena", {}).get("arenaState")
        },
        "attendance": game.get("attendance"),
        "players": players
    }

# =========================
# MAIN
# =========================

def main():
    today = date.today()
    day = START_DATE
    written = 0

    while day <= today:
        formatted = day.strftime("%Y%m%d")
        url = SCOREBOARD_URL.format(date=formatted)

        try:
            scoreboard = get_json(url)
        except Exception:
            day += timedelta(days=1)
            continue

        games = scoreboard.get("scoreboard", {}).get("games", [])

        for g in games:
            if g.get("gameStatus") != 3:
                continue

            game_id = g["gameId"]
            filename = filename_from_gameid(game_id)
            path = OUT_DIR / filename

            if path.exists():
                continue

            try:
                time.sleep(0.4)
                box = get_json(BOXSCORE_URL.format(gameId=game_id))
                game_data = build_game(box)

                with open(path, "w", encoding="utf-8") as f:
                    json.dump(game_data, f, indent=2)

                print("Created:", filename)
                written += 1

            except Exception as e:
                print("Failed:", game_id, e)

        day += timedelta(days=1)

    print("Done. New games written:", written)


if __name__ == "__main__":
    main()
