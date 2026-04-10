import requests
import json
from pathlib import Path

print("NHL SCORERS ALL SEASONS")

BASE = Path("docs/data/nhl")

SEASONS = list(range(2005, 2027))  # 🔥 start here (reliable NHL data)

MAX_PER_RUN = 300
count = 0

def fetch(url):
    try:
        r = requests.get(url)
        if r.status_code == 200:
            return r.json()
    except:
        return {}
    return {}

for SEASON in SEASONS:

    season_file = BASE / f"seasons/{SEASON}.json"
    box_dir = BASE / f"boxscores/{SEASON}"
    box_dir.mkdir(parents=True, exist_ok=True)

    if not season_file.exists():
        print(f"Skipping {SEASON} (no season file)")
        continue

    games = json.loads(season_file.read_text())

    print(f"\n--- {SEASON} ---")

    for game in games:

        game_id = game.get("game_id") or game.get("id")
        file_path = box_dir / f"{game_id}.json"

        if file_path.exists():
            continue

        print(f"Building {SEASON} - {game_id}")

        pbp = fetch(f"https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play")
        box = fetch(f"https://api-web.nhle.com/v1/gamecenter/{game_id}/boxscore")

        try:
            player_map = {}

            stats = box.get("playerByGameStats", {})

            for side in ["homeTeam", "awayTeam"]:
                team = stats.get(side, {})

                for group in ["forwards", "defense", "goalies"]:
                    for p in team.get(group, []):
                        pid = p.get("playerId")
                        name = p.get("name", {}).get("default")

                        if pid and name:
                            player_map[pid] = name

            plays = pbp.get("plays") or pbp.get("gameData", {}).get("plays") or []

            goals = []

            for play in plays:
                if play.get("typeDescKey") != "goal":
                    continue

                d = play.get("details", {})

                goals.append({
                    "period": play.get("periodDescriptor", {}).get("number"),
                    "time": play.get("timeInPeriod"),
                    "scorer": player_map.get(d.get("scoringPlayerId")),
                    "assists": [
                        player_map.get(a)
                        for a in [d.get("assist1PlayerId"), d.get("assist2PlayerId")]
                        if player_map.get(a)
                    ],
                    "strength": d.get("strength")
                })

            game_json = {
                "game_id": game_id,
                "date": game["date"],
                "home_team": game["home_team"],
                "away_team": game["away_team"],
                "home_score": game["home_score"],
                "away_score": game["away_score"],
                "goals": goals
            }

            file_path.write_text(json.dumps(game_json, indent=2))

            count += 1

            if count >= MAX_PER_RUN:
                print("Hit run limit — stopping safely")
                exit()

        except Exception as e:
            print(f"FAILED {game_id}: {e}")
            continue

print("DONE")nh
