#!/usr/bin/env python3

import json
import time
from datetime import date, timedelta, datetime
from pathlib import Path
import requests

# ==============================
# CONFIG
# ==============================

SEASON_FOLDER = "2025"
BASE_DIR = Path("docs/data/nba")
OUT_DIR = BASE_DIR / SEASON_FOLDER
OUT_DIR.mkdir(parents=True, exist_ok=True)

SCOREBOARD_URL = "https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_{date}.json"
BOXSCORE_URL = "https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{gameId}.json"

DAYS_TO_CHECK = 7  # number of days to scan each run


# ==============================
# HELPERS
# ==============================

def get_json(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()


def game_type_from_id(game_id):
    prefix = game_id[:3]
    if prefix == "001":
        return "Preseason"
    if prefix == "002":
        return "Regular Season"
    if prefix == "004":
        return "Playoffs"
    if prefix == "005":
        return "Play-In"
    return "Unknown"


def filename_from_gameid(game_id):
    return str(int(game_id)) + ".json"


# ==============================
# BUILD GAME JSON
# ==============================

def build_game(box):
    game = box["game"]
    home = game["homeTeam"]
    away = game["awayTeam"]
    arena = game.get("arena", {})

    home_score = int(home.get("score") or 0)
    away_score = int(away.get("score") or 0)

    winner = ""
    if home_score > away_score:
        winner = home["teamName"]
    elif away_score > home_score:
        winner = away["teamName"]

    players = []

    for team in [away, home]:
        team_name = team["teamName"]
        for p in team.get("players", []):
            stats = p.get("statistics", {})
            minutes = stats.get("minutes", "")
            if not minutes:
                continue

            if ":" in minutes:
                minutes = minutes.split(":")[0]

            players.append({
                "player_id": str(p.get("personId")),
                "player_name": p.get("name"),
                "team": team_name,
                "minutes": minutes,
                "points": int(stats.get("points") or 0),
                "rebounds": int(stats.get("reboundsTotal") or 0),
                "assists": int(stats.get("assists") or 0),
                "steals": int(stats.get("steals") or 0),
                "blocks": int(stats.get("blocks") or 0),
                "turnovers": int(stats.get("turnovers") or 0),
                "fouls": int(stats.get("foulsPersonal") or 0),
                "plus_minus": int(stats.get("plusMinusPoints") or 0),
                "fg_made": int(stats.get("fieldGoalsMade") or 0),
                "fg_attempted": int(stats.get("fieldGoalsAttempted") or 0),
                "three_made": int(stats.get("threePointersMade") or 0),
                "three_attempted": int(stats.get("threePointersAttempted") or 0),
                "ft_made": int(stats.get("freeThrowsMade") or 0),
                "ft_attempted": int(stats.get("freeThrowsAttempted") or 0),
            })

    return {
        "game_id": str(int(game["gameId"])),
        "season": int(SEASON_FOLDER),
        "date": game["gameTimeUTC"].split("T")[0],
        "home_team": home["teamName"],
        "away_team": away["teamName"],
        "home_score": home_score,
        "away_score": away_score,
        "winner": winner,
        "game_type": game_type_from_id(game["gameId"]),
        "game_subtype": "",
        "arena": {
            "arenaId": arena.get("arenaId"),
            "arenaName": arena.get("arenaName"),
            "arenaCity": arena.get("arenaCity"),
            "arenaState": arena.get("arenaState"),
        },
        "attendance": int(game.get("attendance") or 0),
        "players": players
    }


# ==============================
# MAIN
# ==============================

def main():
    today = date.today()

    written = 0

    for i in range(DAYS_TO_CHECK):
        day = today - timedelta(days=i)
        url = SCOREBOARD_URL.format(date=day.strftime("%Y%m%d"))

        try:
            scoreboard = get_json(url)
        except:
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

    print("Done. New games written:", written)


if __name__ == "__main__":
    main()
