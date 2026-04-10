import requests
import json
from pathlib import Path

print("NHL SCORERS ALL SEASONS")

BASE = Path("docs/data/nhl")

# 🔥 Adjust range as needed
SEASONS = list(range(2005, 2027))  # 2005 → 2026

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

        # ✅ skip existing files
        if file_path.exists():
            continue

        print(f"Building {SEASON} - {game_id}")

        pbp = fetch(f"https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play")
        box = fetch(f"https://api-web.nhle.com/v1/gamecenter/{game_id}/boxscore")

        try:
            # 🔥 PLAYER MAP (CORRECT LOCATION)
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

            # 🔥 PLAY DATA (HANDLE BOTH FORMATS)
            plays = pbp.get("plays") or pbp.get("gameData", {}).get("plays") or []

            goals = []

            for play in plays:
                if play.get("typeDescKey") != "goal":
                    continue

                d = play.get("details", {})

                scorer_id = d.get("scoringPlayerId")
                a1 = d.get("assist1PlayerId")
                a2 = d.get("assist2PlayerId")

                goals.append({
                    "period": play.get("periodDescriptor", {}).get("number"),
                    "time": play.get("timeInPeriod"),
                    "scorer": player_map.get(scorer_id),
                    "assists": [
                        player_map.get(a)
                        for a in [a1, a2]
                        if player_map.get(a)
                    ],
                    "strength": d.get("strength")
                })

            game_json = {
                "game_id": game_id,
                "date": game.get("date"),
                "home_team": game.get("home_team"),
                "away_team": game.get("away_team"),
                "home_score": game.get("home_score"),
                "away_score": game.get("away_score"),
                "goals": goals
            }

            file_path.write_text(json.dumps(game_json, indent=2))

            count += 1

            # 🔥 STOP BEFORE TIMEOUT
            if count >= MAX_PER_RUN:
                print("Hit run limit — stopping safely")
                exit()

        except Exception as e:
            print(f"FAILED {game_id}: {e}")
            continue

print("DONE")
