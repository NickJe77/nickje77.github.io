import requests
import json
import zipfile
import io
from pathlib import Path

print("🌍 WORLD CUP BUILDER (CRICSHEET)")

BASE = Path("docs/data/cricket/worldcups")
BASE.mkdir(parents=True, exist_ok=True)

# -----------------------
# DOWNLOAD DATA
# -----------------------
URL = "https://cricsheet.org/downloads/odis_male_json.zip"

print("⬇️ Downloading dataset...")
r = requests.get(URL)

z = zipfile.ZipFile(io.BytesIO(r.content))

matches = []

# -----------------------
# LOOP FILES
# -----------------------
for file in z.namelist():

    if not file.endswith(".json"):
        continue

    data = json.loads(z.read(file))

    info = data.get("info", {})

    # ONLY WORLD CUP
    if "world cup" not in str(info.get("event", "")).lower():
        continue

    teams = info.get("teams", [])
    dates = info.get("dates", [])
    venue = info.get("venue", "")

    outcome = info.get("outcome", {})

    winner = outcome.get("winner", "")
    by = outcome.get("by", {})

    margin = ""
    if "runs" in by:
        margin = f"{by['runs']} runs"
    elif "wickets" in by:
        margin = f"{by['wickets']} wickets"

    if len(teams) != 2:
        continue

    matches.append({
        "date": dates[0] if dates else "",
        "team1": teams[0],
        "team2": teams[1],
        "winner": winner,
        "margin": margin,
        "venue": venue
    })

print("✅ Matches found:", len(matches))

# -----------------------
# SAVE
# -----------------------
out_file = BASE / "world_cups_all.json"

with open(out_file, "w") as f:
    json.dump(matches, f, indent=2)

print("💾 Saved:", out_file)
