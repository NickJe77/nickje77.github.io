import requests
import json
import os

print("NBA updater starting")

BASE_DIR = "docs/data/nba"
os.makedirs(BASE_DIR, exist_ok=True)

schedule_url = "https://cdn.nba.com/static/json/staticData/scheduleLeagueV2.json"

r = requests.get(schedule_url, timeout=30)

if r.status_code != 200:
    print("Schedule download failed")
    raise SystemExit(1)

data = r.json()
game_dates = data["leagueSchedule"]["gameDates"]

games_saved = 0
games_skipped = 0

for d in game_dates:
    for g in d["games"]:

        game_id = str(g["gameId"])

        # Skip preseason
        if game_id.startswith("001"):
            continue

        game_date = g["gameDateEst"]
        year = int(game_date[:4])
        month = int(game_date[5:7])

        # FIXED NBA season logic
        # NBA season = year the season started
        if month >= 10:
            season = year
        else:
            season = year - 1

        season_dir = f"{BASE_DIR}/{season}"
        os.makedirs(season_dir, exist_ok=True)

        game_file = f"{season_dir}/{game_id}.json"

        if os.path.exists(game_file):
            games_skipped += 1
            continue

        box_url = f"https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{game_id}.json"
        box = requests.get(box_url, timeout=30)

        if box.status_code != 200:
            print("Missing boxscore:", game_id)
            continue

        game = box.json()["game"]

        if game_id.startswith("002"):
            game_type = "Regular Season"
        elif game_id.startswith("004"):
            game_type = "Playoffs"
        else:
            game_type = "Other"

        output = {
            "game_id": game_id,
            "date": game.get("gameTimeUTC", ""),
            "game_type": game_type,
            "home_team": game["homeTeam"].get("teamName", ""),
            "away_team": game["awayTeam"].get("teamName", ""),
            "home_score": game["homeTeam"].get("score", 0),
            "away_score": game["awayTeam"].get("score", 0),
            "arena": game.get("arena", {}).get("arenaName", ""),
            "players": []
        }

        for team_key in ["homeTeam", "awayTeam"]:
            team = game.get(team_key, {})
            team_name = team.get("teamName", "")

            for p in team.get("players", []):
                stats = p.get("statistics", {})

                output["players"].append({
                    "player": p.get("name", ""),
                    "team": team_name,
                    "minutes": stats.get("minutes", "0"),
                    "points": stats.get("points", 0),
                    "rebounds": stats.get("reboundsTotal", 0),
                    "assists": stats.get("assists", 0),
                    "steals": stats.get("steals", 0),
                    "blocks": stats.get("blocks", 0),
                    "turnovers": stats.get("turnovers", 0),
                    "fgm": stats.get("fieldGoalsMade", 0),
                    "fga": stats.get("fieldGoalsAttempted", 0),
                    "tpm": stats.get("threePointersMade", 0),
                    "tpa": stats.get("threePointersAttempted", 0),
                    "ftm": stats.get("freeThrowsMade", 0),
                    "fta": stats.get("freeThrowsAttempted", 0)
                })

        with open(game_file, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)

        index_path = f"{season_dir}/index.json"

        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                index = json.load(f)
        else:
            index = {"games": []}

        if game_id not in index["games"]:
            index["games"].append(game_id)

        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2)

        games_path = f"{season_dir}/games.json"

        if os.path.exists(games_path):
            with open(games_path, "r", encoding="utf-8") as f:
                games_list = json.load(f)
        else:
            games_list = []

        games_list.append({
            "game_id": game_id,
            "date": output["date"],
            "game_type": game_type,
            "home_team": output["home_team"],
            "away_team": output["away_team"],
            "home_score": output["home_score"],
            "away_score": output["away_score"]
        })

        with open(games_path, "w", encoding="utf-8") as f:
            json.dump(games_list, f, indent=2)

        games_saved += 1
        print("Saved", game_file)

print("Games saved:", games_saved)
print("Games skipped:", games_skipped)
print("NBA updater finished")
