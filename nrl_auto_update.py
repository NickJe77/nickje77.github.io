import json
import requests
from pathlib import Path
from datetime import datetime

print("NRL UPDATE WITH PLAYER STATS")

SEASON = 2026

BASE = Path("docs/data/nrl")
SEASON_FILE = BASE / "seasons" / f"{SEASON}.json"
INDEX_FILE = BASE / "index.json"

BASE.mkdir(parents=True, exist_ok=True)
SEASON_FILE.parent.mkdir(parents=True, exist_ok=True)

headers = {"User-Agent": "Mozilla/5.0"}

def get_round(round_name):

    url = f"https://www.nrl.com/draw/data?competition=111&season={SEASON}&round={round_name}"

    r = requests.get(url, headers=headers, timeout=30)

    if r.status_code != 200:
        return []

    data = r.json()

    return data.get("fixtures", [])


print("Downloading fixtures")

fixtures = []
fixtures += get_round("opening")
fixtures += get_round("all")

print("Fixtures detected:", len(fixtures))

games = []

today = datetime.utcnow().date()

for m in fixtures:

    # Safe match ID handling
    match_id = m.get("matchId") or m.get("id")

    if not match_id:
        continue

    home = m.get("homeTeam", {}).get("nickName")
    away = m.get("awayTeam", {}).get("nickName")

    if not home or not away:
        continue

    round_title = m.get("roundTitle", "")

    if "Opening" in round_title:
        round_num = 1
    elif round_title.startswith("Round"):
        try:
            round_num = int(round_title.split()[1])
        except:
            round_num = 0
    else:
        round_num = 0

    kickoff = m.get("clock", {}).get("kickOffTimeLong", "")
    date_iso = kickoff[:10] if kickoff else ""

    # Skip future games (keeps season page clean)
    try:
        game_date = datetime.strptime(date_iso, "%Y-%m-%d").date()
        if game_date > today:
            continue
    except:
        pass

    venue = m.get("venue", "")

    home_pts = m.get("homeScore", 0)
    away_pts = m.get("awayScore", 0)

    game = {
        "match_id": match_id,
        "season": SEASON,
        "round": round_num,
        "date_iso": date_iso,
        "venue": venue,
        "home_team": home,
        "away_team": away,
        "home_points": home_pts,
        "away_points": away_pts,
        "players": []
    }

    # Pull player stats
    try:

        stats_url = f"https://stats.nrl.com/api/match/{match_id}"

        s = requests.get(stats_url, headers=headers, timeout=30)

        if s.status_code == 200:

            stats = s.json()

            for team in stats.get("teams", []):

                team_name = team.get("nickName")

                for p in team.get("players", []):

                    game["players"].append({

                        "name": p.get("fullName"),
                        "team": team_name,
                        "position": p.get("position"),
                        "tries": p.get("tries", 0),
                        "tackles": p.get("tackles", 0),
                        "run_metres": p.get("runMetres", 0),
                        "line_breaks": p.get("lineBreaks", 0)

                    })

    except Exception as e:
        print("Stats fetch failed for", match_id)

    games.append(game)


games.sort(key=lambda x: (x["round"], x["date_iso"]))


with open(SEASON_FILE, "w") as f:
    json.dump(games, f, indent=2)


print("Season written:", SEASON_FILE)


# Update index.json
if INDEX_FILE.exists():

    with open(INDEX_FILE) as f:
        index = json.load(f)

else:

    index = {}


if "seasons" not in index:
    index["seasons"] = []

if SEASON not in index["seasons"]:
    index["seasons"].append(SEASON)

index["seasons"] = sorted(index["seasons"])


with open(INDEX_FILE, "w") as f:
    json.dump(index, f, indent=2)


print("Index updated")
print("Games written:", len(games))
print("Update complete")
