import requests
import zipfile
import io
import os
from pathlib import Path

SEASON = 2026

OUTPUT_DIR = Path(f"docs/data/baseball/boxscores/{SEASON}")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

RETRO_URL = f"https://www.retrosheet.org/events/{SEASON}eve.zip"

print(f"DOWNLOADING RETROSHEET {SEASON}...")

r = requests.get(RETRO_URL)
z = zipfile.ZipFile(io.BytesIO(r.content))

# -----------------------------------------
# HELPERS
# -----------------------------------------
def parse_event(parts):
    # play,inning,half,player,count,pitches,result
    return [
        "play",
        parts[1],
        parts[2],
        parts[3],
        parts[4],
        parts[5],
        parts[6]
    ]

# -----------------------------------------
# PROCESS FILES
# -----------------------------------------
games = {}

for filename in z.namelist():
    if not filename.endswith(".EVN") and not filename.endswith(".EVA"):
        continue

    with z.open(filename) as f:
        lines = f.read().decode("latin-1").splitlines()

    current_game = None

    for line in lines:
        parts = line.split(",")

        if parts[0] == "id":
            current_game = parts[1]

            games[current_game] = {
                "game_id": current_game,
                "date": "",
                "season": SEASON,
                "home_code": "",
                "away_code": "",
                "home_team": "",
                "away_team": "",
                "events": []
            }

        elif parts[0] == "info":
            key = parts[1]
            val = parts[2]

            if key == "date":
                games[current_game]["date"] = val

            elif key == "visteam":
                games[current_game]["away_code"] = val
                games[current_game]["away_team"] = val

            elif key == "hometeam":
                games[current_game]["home_code"] = val
                games[current_game]["home_team"] = val

        elif parts[0] == "play":
            event = parse_event(parts)
            games[current_game]["events"].append(event)

# -----------------------------------------
# SAVE FILES
# -----------------------------------------
print("SAVING GAMES...")

for game_id, game in games.items():
    out_file = OUTPUT_DIR / f"{game_id}.json"

    with open(out_file, "w") as f:
        import json
        json.dump(game, f)

print("DONE ✅")
