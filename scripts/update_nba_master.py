import json
import requests
import time
from pathlib import Path
from datetime import date, timedelta

START_DATE = date(2025, 2, 15)

SCOREBOARD_URL = "https://cdn.nba.com/static/json/liveData/scoreboard/scoreboard_{date}.json"
BOXSCORE_URL = "https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{gameId}.json"

HEADERS = {"User-Agent": "Mozilla/5.0"}

BASE_DIR = Path("docs/data/nba")


def get_json(url):
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.json()


def determine_season(game_date_str):
    year = int(game_date_str[:4])
    month = int(game_date_str[5:7])

    # NBA season starts in October
    if month >= 10:
        return year
    else:
        return year - 1


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

    return game, {
        "game_id": game["gameId"],
        "season": determine_season(game["gameDate"]),
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


def main():
    today = date.today()
    day = START_DATE
    written = 0

    while day <= today:
        formatted = day.strftime("%Y%m%d")
        url = SCOREBOARD_URL.format(date=formatted)

        try:
            scoreboard = get_json(url)
        except:
            day += timedelta(days=1)
            continue

        games = scoreboard.get("scoreboard", {}).get("games", [])

        for g in games:
            if g.get("gameStatus") != 3:
                continue

            game_id = g["gameId"]

            time.sleep(0.4)
            box = get_json(BOXSCORE_URL.format(gameId=game_id))

            game_meta, game_data = build_game(box)

            season = determine_season(game_meta["gameDate"])
            season_dir = BASE_DIR / str(season)
            season_dir.mkdir(parents=True, exist_ok=True)

            path = season_dir / f"{game_id}.json"

            if path.exists():
                continue

            with open(path, "w", encoding="utf-8") as f:
                json.dump(game_data, f, indent=2)

            print("Created:", path)
            written += 1

        day += timedelta(days=1)

    print("Done. New games written:", written)


if __name__ == "__main__":
    main()
