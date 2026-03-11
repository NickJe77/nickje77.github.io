import requests
import json
import os
from datetime import datetime, timezone

BASE_DIR = "docs/data/nba"

print("NBA download boxscores starting")

today = datetime.now(timezone.utc)


def convert_minutes(raw):
    if not raw:
        return "0:00"

    if isinstance(raw, str) and raw.startswith("PT"):
        try:
            cleaned = raw.replace("PT", "").replace("S", "")
            parts = cleaned.split("M")
            mins = int(parts[0] or "0")
            secs = int(float(parts[1] or "0"))
            return f"{mins}:{secs:02d}"
        except:
            return "0:00"

    return str(raw)


def clean_name(player):
    first = player.get("firstName", "")
    last = player.get("familyName", "")

    if first or last:
        return f"{first} {last}".strip()

    if player.get("name"):
        return player["name"]

    if player.get("nameI"):
        return player["nameI"]

    return "Unknown"


games_saved = 0
games_skipped = 0

for season in os.listdir(BASE_DIR):

    season_path = os.path.join(BASE_DIR, season)

    if not season.isdigit():
        continue

    index_path = os.path.join(season_path, "index.json")

    if not os.path.exists(index_path):
        continue

    with open(index_path) as f:
        index = json.load(f)

    for game_id in index["games"]:

        if game_id.startswith("001"):
            continue

        box_url = f"https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{game_id}.json"

        r = requests.get(box_url, timeout=30)

        if r.status_code != 200:
            games_skipped += 1
            continue

        game = r.json()["game"]

        game_time = game.get("gameTimeUTC")

        if game_time:
            try:
                game_dt = datetime.fromisoformat(game_time.replace("Z","+00:00"))
                if game_dt > today:
                    continue
            except:
                pass

        home = game["homeTeam"]
        away = game["awayTeam"]

        home_team = f'{home.get("teamCity","")} {home.get("teamName","")}'.strip()
        away_team = f'{away.get("teamCity","")} {away.get("teamName","")}'.strip()

        output = {
            "game_id": game_id,
            "date": game_time,
            "game_type": "Regular Season",
            "home_team": home_team,
            "away_team": away_team,
            "home_score": home.get("score",0),
            "away_score": away.get("score",0),
            "arena": game.get("arena",{}).get("arenaName",""),
            "players":[]
        }

        for team_key in ["homeTeam","awayTeam"]:

            team = game.get(team_key,{})
            team_name = f'{team.get("teamCity","")} {team.get("teamName","")}'.strip()

            for p in team.get("players",[]):

                stats = p.get("statistics",{})

                output["players"].append({
                    "player": clean_name(p),
                    "team": team_name,
                    "minutes": convert_minutes(stats.get("minutes")),
                    "points": stats.get("points",0),
                    "rebounds": stats.get("reboundsTotal",0),
                    "assists": stats.get("assists",0),
                    "steals": stats.get("steals",0),
                    "blocks": stats.get("blocks",0),
                    "turnovers": stats.get("turnovers",0)
                })

        game_file = os.path.join(season_path, f"{game_id}.json")

        with open(game_file,"w") as f:
            json.dump(output,f,indent=2)

        games_saved += 1
        print("Saved",game_file)

print("Games saved:",games_saved)
print("Games skipped:",games_skipped)
print("NBA download boxscores finished")
