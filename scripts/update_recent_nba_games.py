import json
import os
from datetime import datetime, timedelta, timezone

import requests

START_DATE = datetime(2026, 2, 16, tzinfo=timezone.utc)
TODAY = datetime.now(timezone.utc)

OUTPUT_DIR = "docs/data/nba/2026"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0"
})

def get_games(date_obj):
    ds = date_obj.strftime("%Y%m%d")
    url = f"https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_{ds}.json"
    r = SESSION.get(url, timeout=30)

    if r.status_code != 200:
        print(f"No scoreboard {ds} ({r.status_code})")
        return []

    data = r.json()
    scoreboard = data.get("scoreboard", {})
    games = scoreboard.get("games", [])

    print(f"Checking {ds} - games: {len(games)}")
    return games

def get_boxscore(game_id):
    url = f"https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{game_id}.json"
    r = SESSION.get(url, timeout=30)

    if r.status_code != 200:
        print(f"Boxscore failed {game_id} ({r.status_code})")
        return None

    return r.json()

def safe_int(v):
    if v in (None, "", " "):
        return 0
    try:
        return int(v)
    except Exception:
        try:
            return int(float(v))
        except Exception:
            return 0

date_obj = START_DATE

while date_obj <= TODAY:
    games = get_games(date_obj)

    for g in games:
        game_id = str(g.get("gameId", ""))

        if not game_id:
            continue

        file_path = os.path.join(OUTPUT_DIR, f"{game_id}.json")

        if os.path.exists(file_path):
            continue

        box = get_boxscore(game_id)
        if not box:
            continue

        game = box.get("game", {})
        home_team = game.get("homeTeam", {})
        away_team = game.get("awayTeam", {})
        arena = game.get("arena", {})

        out = {
            "game_id": game_id,
            "season": 2026,
            "date": game.get("gameEt") or game.get("gameTimeUTC") or "",
            "home_team": home_team.get("teamName", ""),
            "away_team": away_team.get("teamName", ""),
            "home_score": safe_int(home_team.get("score")),
            "away_score": safe_int(away_team.get("score")),
            "arena": arena.get("arenaName", ""),
            "players": []
        }

        for side_key in ["homeTeam", "awayTeam"]:
            team = game.get(side_key, {})
            team_name = team.get("teamName", "")

            for p in team.get("players", []):
                stats = p.get("statistics", {}) or {}
                name = p.get("name")

                if isinstance(name, dict):
                    player_name = name.get("default") or name.get("display") or ""
                else:
                    player_name = name or ""

                out["players"].append({
                    "player": player_name,
                    "team": team_name,
                    "minutes": stats.get("minutes", "0"),
                    "points": safe_int(stats.get("points")),
                    "rebounds": safe_int(stats.get("reboundsTotal")),
                    "assists": safe_int(stats.get("assists")),
                    "steals": safe_int(stats.get("steals")),
                    "blocks": safe_int(stats.get("blocks")),
                    "turnovers": safe_int(stats.get("turnovers")),
                    "fgm": safe_int(stats.get("fieldGoalsMade")),
                    "fga": safe_int(stats.get("fieldGoalsAttempted")),
                    "tpm": safe_int(stats.get("threePointersMade")),
                    "tpa": safe_int(stats.get("threePointersAttempted")),
                    "ftm": safe_int(stats.get("freeThrowsMade")),
                    "fta": safe_int(stats.get("freeThrowsAttempted"))
                })

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2)

        print(f"Saved {file_path}")

    date_obj += timedelta(days=1)

print("NBA update finished")
