import os
import json
import requests

DIR = "docs/data/baseball/boxscores/2026"

# 🔥 SAME TEAM ID MAP (bulletproof)
TEAM_ID_MAP = {
    109:"ARI", 144:"ATL", 110:"BAL", 111:"BOS", 112:"CHC", 145:"CHW",
    113:"CIN", 114:"CLE", 115:"COL", 116:"DET", 117:"HOU", 118:"KAN",
    108:"LAA", 119:"LOS", 146:"MIA", 158:"MIL", 142:"MIN", 121:"NEW",
    147:"NEW", 133:"ATH", 143:"PHI", 134:"PIT", 135:"SAN", 137:"SAN",
    136:"SEA", 138:"ST", 139:"TAM", 140:"TEX", 141:"TOR", 120:"WAS"
}

fixed = 0
skipped = 0

for file in os.listdir(DIR):

    if not file.endswith(".json"):
        continue

    # skip already good files
    if "__" not in file and "UNK" not in file:
        continue

    path = os.path.join(DIR, file)

    print("Fixing:", file)

    try:
        with open(path) as f:
            data = json.load(f)

        # -------------------------
        # GET GAME ID
        # -------------------------
        game_id = (
            data.get("gamePk")
            or data.get("gameData", {}).get("game", {}).get("pk")
        )

        if not game_id:
            print("❌ No gamePk:", file)
            skipped += 1
            continue

        # -------------------------
        # FETCH CLEAN GAME DATA
        # -------------------------
        url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&gamePk={game_id}"
        res = requests.get(url)

        if res.status_code != 200:
            print("❌ API fail:", game_id)
            skipped += 1
            continue

        sched = res.json()

        dates = sched.get("dates", [])
        if not dates:
            print("❌ No schedule data:", game_id)
            skipped += 1
            continue

        game = dates[0]["games"][0]

        date_str = game.get("gameDate", "")[:10]

        teams = game.get("teams", {})
        home = teams.get("home", {})
        away = teams.get("away", {})

        home_id = home.get("team", {}).get("id")
        away_id = away.get("team", {}).get("id")

        home_code = TEAM_ID_MAP.get(home_id)
        away_code = TEAM_ID_MAP.get(away_id)

        if not home_code or not away_code:
            print("❌ Missing codes:", game_id)
            skipped += 1
            continue

        new_name = f"{date_str}_{away_code}_{home_code}.json"
        new_path = os.path.join(DIR, new_name)

        os.rename(path, new_path)

        print("✅ Renamed →", new_name)
        fixed += 1

    except Exception as e:
        print("❌ Error:", file, str(e))
        skipped += 1

print("\n====================")
print("Fixed:", fixed)
print("Skipped:", skipped)
print("====================")
