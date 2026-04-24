import requests
import json
import zipfile
import io
from pathlib import Path
from collections import defaultdict

print("🌍 WORLD CUP BUILDER (WITH PLAYER STATS)")

BASE = Path("docs/data/cricket/worldcups")
BASE.mkdir(parents=True, exist_ok=True)

URL = "https://cricsheet.org/downloads/odis_male_json.zip"

r = requests.get(URL)
z = zipfile.ZipFile(io.BytesIO(r.content))

matches = []

for file in z.namelist():

    if not file.endswith(".json"):
        continue

    data = json.loads(z.read(file))
    info = data.get("info", {})

    event = str(info.get("event", "")).lower()

    # ✅ FILTER WORLD CUP ONLY
    if "world cup" not in event:
        continue
    if "qualifier" in event:
        continue

    teams = info.get("teams", [])
    dates = info.get("dates", [])
    venue = info.get("venue", "")

    if len(teams) != 2:
        continue

    scores = {}
    bat_stats = defaultdict(int)
    bowl_stats = defaultdict(int)

    # -----------------------
    # PROCESS INNINGS
    # -----------------------
    for inn in data.get("innings", []):

        team = inn.get("team")
        runs = 0
        wickets = 0

        for over in inn.get("overs", []):
            for ball in over.get("deliveries", []):

                # total runs
                runs += ball.get("runs", {}).get("total", 0)

                # batsman runs
                batter = ball.get("batter")
                bat_runs = ball.get("runs", {}).get("batter", 0)

                if batter:
                    bat_stats[batter] += bat_runs

                # wickets
                if "wickets" in ball:
                    wickets += len(ball["wickets"])

                    for w in ball["wickets"]:
                        bowler = ball.get("bowler")
                        if bowler:
                            bowl_stats[bowler] += 1

        scores[team] = f"{runs}/{wickets}"

    # -----------------------
    # TOP PLAYERS
    # -----------------------
    top_batter = ""
    top_runs = 0

    for p, r in bat_stats.items():
        if r > top_runs:
            top_runs = r
            top_batter = p

    top_bowler = ""
    top_wkts = 0

    for p, w in bowl_stats.items():
        if w > top_wkts:
            top_wkts = w
            top_bowler = p

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

    matches.append({
        "date": dates[0] if dates else "",
        "team1": teams[0],
        "team2": teams[1],
        "team1_score": scores.get(teams[0], ""),
        "team2_score": scores.get(teams[1], ""),
        "winner": winner,
        "margin": margin,
        "venue": venue,
        "top_batter": f"{top_batter} ({top_runs})" if top_batter else "",
        "top_bowler": f"{top_bowler} ({top_wkts})" if top_bowler else ""
    })

print("✅ Matches:", len(matches))

# -----------------------
# SAVE
# -----------------------
out_file = BASE / "world_cup_full.json"

with open(out_file, "w") as f:
    json.dump(matches, f, indent=2)

print("💾 Saved:", out_file)
