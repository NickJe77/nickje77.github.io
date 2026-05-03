import requests
import zipfile
import io
import os
import json
import time

OUTPUT = "docs/data/cricket/world_cups"
os.makedirs(OUTPUT, exist_ok=True)

CRICSHEET_URL = "https://cricsheet.org/downloads/odis_json.zip"

# -----------------------------
# SAFE WRITE (NO OVERWRITE)
# -----------------------------
def safe_write(path, data):
    if os.path.exists(path):
        return
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# -----------------------------
# BUILD FROM CRICSHEET (2000+)
# -----------------------------
def build_from_cricsheet():

    print("Downloading Cricsheet...")
    r = requests.get(CRICSHEET_URL, timeout=60)

    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall("cricsheet_tmp")

    built = 0

    for file in os.listdir("cricsheet_tmp"):

        if not file.endswith(".json"):
            continue

        path = os.path.join("cricsheet_tmp", file)

        with open(path) as f:
            data = json.load(f)

        info = data.get("info", {})
        event = info.get("event", {}).get("name", "")

        # ONLY WORLD CUPS
        if "World Cup" not in event:
            continue

        date = info.get("dates", [""])[0]
        year = date[:4] if date else "unknown"

        folder = f"{OUTPUT}/{year}"
        os.makedirs(folder, exist_ok=True)

        match_id = file.replace(".json", "")
        file_path = f"{folder}/{match_id}.json"

        if os.path.exists(file_path):
            continue

        match = {
            "match": " vs ".join(info.get("teams", [])),
            "date": date,
            "venue": info.get("venue", ""),
            "result": info.get("outcome", {}),
            "innings": []
        }

        # -----------------------------
        # BUILD INNINGS (FIXED LOGIC)
        # -----------------------------
        for inn in data.get("innings", []):

            team = list(inn.keys())[0]
            details = inn[team]

            inning = {
                "team": team,
                "batting": {},
                "bowling": {}
            }

            deliveries = []

            # HANDLE BOTH FORMATS
            if isinstance(details, dict):
                if "overs" in details:
                    for over in details.get("overs", []):
                        deliveries.extend(over.get("deliveries", []))
                elif "deliveries" in details:
                    deliveries = details.get("deliveries", [])
                else:
                    continue
            else:
                continue

            # PROCESS BALLS
            for delivery in deliveries:
                for ball in delivery.values():

                    batter = ball.get("batter")
                    bowler = ball.get("bowler")

                    runs_b = ball.get("runs", {}).get("batter", 0)
                    runs_t = ball.get("runs", {}).get("total", 0)

                    # -----------------
                    # BATTING
                    # -----------------
                    if batter:
                        b = inning["batting"].setdefault(batter, {
                            "runs": 0,
                            "balls": 0,
                            "fours": 0,
                            "sixes": 0,
                            "out": ""
                        })

                        b["runs"] += runs_b
                        b["balls"] += 1

                        if runs_b == 4:
                            b["fours"] += 1
                        if runs_b == 6:
                            b["sixes"] += 1

                    # -----------------
                    # BOWLING
                    # -----------------
                    if bowler:
                        bl = inning["bowling"].setdefault(bowler, {
                            "runs": 0,
                            "wickets": 0
                        })

                        bl["runs"] += runs_t

                    # -----------------
                    # WICKETS
                    # -----------------
                    if "wickets" in ball:
                        for w in ball["wickets"]:

                            out_p = w.get("player_out")
                            kind = w.get("kind", "")

                            if out_p and out_p in inning["batting"]:
                                inning["batting"][out_p]["out"] = kind

                            if bowler:
                                inning["bowling"][bowler]["wickets"] += 1

            match["innings"].append(inning)

        safe_write(file_path, match)
        built += 1

    print(f"\nCricsheet built: {built} matches")


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    build_from_cricsheet()
    print("Done.")
