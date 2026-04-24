import requests
import json
import zipfile
import io
from pathlib import Path

print("🌍 WORLD CUP BUILDER (WITH SCORES)")

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

    # ✅ ONLY MAIN WORLD CUP
    if "world cup" not in event:
        continue
    if "qualifier" in event:
        continue

    teams = info.get("teams", [])
    dates = info.get("dates", [])
    venue = info.get("venue", "")

    if len(teams) != 2:
        continue

    # -----------------------
    # 🏏 GET SCORES FROM INNINGS
    # -----------------------
    scores = {}

    for inn in data.get("innings", []):

        team = inn.get("team")
        runs = 0
        wickets = 0

        for over in inn.get("overs", []):
            for ball in over.get("deliveries", []):
                runs += ball.get("runs", {}).get("total", 0)

                if "wickets" in ball:
                    wickets += len(ball["wickets"])

        scores[team] = f"{runs}/{wickets}"

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
        "venue": venue
    })

print("✅ Matches:", len(matches))

# -----------------------
# SAVE
# -----------------------
out_file = BASE / "world_cup_with_scores.json"

with open(out_file, "w") as f:
    json.dump(matches, f, indent=2)

print("💾 Saved:", out_file)
