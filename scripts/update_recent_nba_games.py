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


def convert_minutes(raw):
    if not raw:
        return "0:00"

    if raw.startswith("PT"):
        try:
            m = raw.replace("PT", "").replace("S", "").split("M")
            minutes = int(m[0])
            seconds = int(float(m[1]))
            return f"{minutes}:{seconds:02d}"
        except:
            return "0:00"

    return raw


for d in game_dates:
    for g in d["games"]:

        game_id = str(g["gameId"])

        # skip preseason
        if game_id.startswith("001"):
            continue

        game_date = g["gameDateEst"]
        year = int(game_date[:4])
        month = int(game_date[5:7])

        # NBA season logic
        if month >= 10:
            season = year
        else:
            season = year - 1

        season_dir = f"{BASE_DIR}/{season}"
        os.makedirs(season_dir, exist_ok=True)

        game_file = f"{season_dir}/{game_id}.json"

        box_url = f"https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{game_id}.json"
        box = requests.get(box_url, timeout=30)

        if box.status_code != 200:
            print("Missing boxscore:", game_id)
            continue

        game = box.json()["game"]

        home = game["homeTeam"]
        away = game["awayTeam"]

        home_team = f'{home.get("teamCity","")} {home.get("teamName","")}'.strip()
        away_team = f'{away.get("teamCity","")} {away.get("teamName","")}'.strip()

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
            "home_team": home_team,
            "away_team": away_team,
            "home_score": home.get("score", 0),
            "away_score": away.get("score", 0),
            "arena": game.get("arena", {}).get("arenaName", ""),
            "players": []
        }

        for team_key in ["homeTeam", "awayTeam"]:

            team = game.get(team_key, {})
            team_name = f'{team.get("teamCity","")} {team.get("teamName","")}'.strip()

            for p in team.get("players", []):

                stats = p.get("statistics", {})

                # PLAYER NAME FIX (works for old + new NBA API formats)
                player_name = (
                    f"{p.get('firstName','')} {p.get('familyName','')}".strip()
                    or p.get("name")
                    or p.get("nameI")
                    or "Unknown"
                )

                minutes = convert_minutes(stats.get("minutes"))

                output["players"].append({
                    "player": player_name,
                    "team": team_name,
                    "minutes": minutes,
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

        games_saved += 1
        print("Saved", game_file)

print("Games saved:", games_saved)
print("NBA updater finished")
