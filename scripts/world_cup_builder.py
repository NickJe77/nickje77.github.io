import requests
import json
import zipfile
import io
from pathlib import Path
from collections import defaultdict
import hashlib

print("🌍 WORLD CUP FULL SYSTEM")

BASE = Path("docs/data/cricket/worldcups")
BASE.mkdir(parents=True, exist_ok=True)

URL = "https://cricsheet.org/downloads/odis_male_json.zip"

r = requests.get(URL)
z = zipfile.ZipFile(io.BytesIO(r.content))

season_index = []

# -----------------------
# LOOP MATCHES
# -----------------------
for file in z.namelist():

    if not file.endswith(".json"):
        continue

    data = json.loads(z.read(file))
    info = data.get("info", {})

    event = str(info.get("event", "")).lower()

    # ✅ ONLY REAL WORLD CUP
    if "world cup" not in event:
        continue
    if "qualifier" in event:
        continue

    teams = info.get("teams", [])
    dates = info.get("dates", [])
    venue = info.get("venue", "")

    if len(teams) != 2:
        continue

    match_id = hashlib.md5(file.encode()).hexdigest()[:10]

    innings_data = []

    # -----------------------
    # BUILD INNINGS
    # -----------------------
    for inn in data.get("innings", []):

        team = inn.get("team")

        batting = defaultdict(lambda: {
            "runs": 0,
            "balls": 0,
            "fours": 0,
            "sixes": 0,
            "out": False
        })

        bowling = defaultdict(lambda: {
            "balls": 0,
            "runs": 0,
            "wickets": 0
        })

        total_runs = 0
        total_wkts = 0

        for over in inn.get("overs", []):
            for ball in over.get("deliveries", []):

                batter = ball.get("batter")
                bowler = ball.get("bowler")

                runs = ball.get("runs", {})
                bat_runs = runs.get("batter", 0)
                total = runs.get("total", 0)

                total_runs += total

                # -----------------------
                # BATTING
                # -----------------------
                if batter:
                    batting[batter]["runs"] += bat_runs
                    batting[batter]["balls"] += 1

                    if bat_runs == 4:
                        batting[batter]["fours"] += 1
                    if bat_runs == 6:
                        batting[batter]["sixes"] += 1

                # -----------------------
                # BOWLING
                # -----------------------
                if bowler:
                    bowling[bowler]["balls"] += 1
                    bowling[bowler]["runs"] += total

                # -----------------------
                # WICKETS
                # -----------------------
                if "wickets" in ball:
                    total_wkts += len(ball["wickets"])

                    for w in ball["wickets"]:
                        player_out = w.get("player_out")
                        if player_out:
                            batting[player_out]["out"] = True

                        if bowler:
                            bowling[bowler]["wickets"] += 1

        # convert balls → overs
        for b in bowling.values():
            b["overs"] = f"{b['balls']//6}.{b['balls']%6}"
            del b["balls"]

        innings_data.append({
            "team": team,
            "score": f"{total_runs}/{total_wkts}",
            "batting": dict(batting),
            "bowling": dict(bowling)
        })

    # -----------------------
    # RESULT
    # -----------------------
    outcome = info.get("outcome", {})
    winner = outcome.get("winner", "")
    by = outcome.get("by", {})

    margin = ""
    if "runs" in by:
        margin = f"{by['runs']} runs"
    elif "wickets" in by:
        margin = f"{by['wickets']} wickets"

    match = {
        "match_id": match_id,
        "date": dates[0] if dates else "",
        "team1": teams[0],
        "team2": teams[1],
        "venue": venue,
        "winner": winner,
        "margin": margin,
        "innings": innings_data
    }

    # -----------------------
    # SAVE MATCH FILE
    # -----------------------
    year = match["date"][:4]
    year_path = BASE / year
    year_path.mkdir(parents=True, exist_ok=True)

    match_file = year_path / f"{match_id}.json"

    with open(match_file, "w") as f:
        json.dump(match, f, indent=2)

    # -----------------------
    # ADD TO SEASON INDEX
    # -----------------------
    season_index.append({
        "match_id": match_id,
        "date": match["date"],
        "team1": match["team1"],
        "team2": match["team2"],
        "winner": match["winner"]
    })

# -----------------------
# SAVE SEASON INDEX
# -----------------------
index_file = BASE / "index.json"

with open(index_file, "w") as f:
    json.dump(season_index, f, indent=2)

print("✅ DONE")
print("Matches built:", len(season_index))
