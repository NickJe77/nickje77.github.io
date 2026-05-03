import requests
import zipfile
import io
import os
import json

OUTPUT = "docs/data/cricket/world_cups"
os.makedirs(OUTPUT, exist_ok=True)

URL = "https://cricsheet.org/downloads/odis_json.zip"

print("Downloading Cricsheet ODI dataset...")
r = requests.get(URL)

z = zipfile.ZipFile(io.BytesIO(r.content))
z.extractall("cricsheet_temp")

print("Extracted")

count = 0

for file in os.listdir("cricsheet_temp"):

    if not file.endswith(".json"):
        continue

    path = os.path.join("cricsheet_temp", file)

    with open(path) as f:
        data = json.load(f)

    info = data.get("info", {})
    event = info.get("event", {}).get("name", "")

    # ONLY WORLD CUPS
    if "World Cup" not in event:
        continue

    year = str(info.get("dates", [""])[0])[:4]

    folder = f"{OUTPUT}/{year}"
    os.makedirs(folder, exist_ok=True)

    match_id = file.replace(".json", "")
    file_path = f"{folder}/{match_id}.json"

    # SAFE MODE
    if os.path.exists(file_path):
        continue

    match = {
        "match": " vs ".join(info.get("teams", [])),
        "date": info.get("dates", [""])[0],
        "venue": info.get("venue", ""),
        "result": info.get("outcome", {}),
        "innings": []
    }

    # -----------------------------
    # BUILD INNINGS (FULL DETAIL)
    # -----------------------------
    for inn in data.get("innings", []):

        team = list(inn.keys())[0]
        details = inn[team]

        inning = {
            "team": team,
            "batting": {},
            "bowling": {}
        }

        # Track stats
        for over in details.get("overs", []):
            for delivery in over.get("deliveries", []):

                for ball in delivery.values():

                    batter = ball.get("batter")
                    bowler = ball.get("bowler")
                    runs = ball.get("runs", {}).get("batter", 0)

                    # BATTING
                    if batter:
                        if batter not in inning["batting"]:
                            inning["batting"][batter] = {
                                "runs": 0,
                                "balls": 0,
                                "fours": 0,
                                "sixes": 0,
                                "out": ""
                            }

                        inning["batting"][batter]["runs"] += runs
                        inning["batting"][batter]["balls"] += 1

                        if runs == 4:
                            inning["batting"][batter]["fours"] += 1
                        if runs == 6:
                            inning["batting"][batter]["sixes"] += 1

                    # BOWLING
                    if bowler:
                        if bowler not in inning["bowling"]:
                            inning["bowling"][bowler] = {
                                "runs": 0,
                                "wickets": 0
                            }

                        inning["bowling"][bowler]["runs"] += ball.get("runs", {}).get("total", 0)

                    # WICKETS
                    if "wickets" in ball:
                        for w in ball["wickets"]:
                            player_out = w.get("player_out")
                            kind = w.get("kind")

                            if player_out and player_out in inning["batting"]:
                                inning["batting"][player_out]["out"] = kind

                            if bowler:
                                inning["bowling"][bowler]["wickets"] += 1

        match["innings"].append(inning)

    # SAVE
    with open(file_path, "w") as f:
        json.dump(match, f, indent=2)

    count += 1

print(f"\nSaved {count} World Cup matches with full scorecards")
