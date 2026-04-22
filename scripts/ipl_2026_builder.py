import requests
import json
from datetime import datetime

print("IPL 2026 BUILDER STARTING")

OUTPUT = "docs/data/ipl/ipl_2026.json"

# ✅ Known working base (schedule IDs)
MATCH_IDS = [
    70343128,70343130,70343132,70343134,70343136,70343138,
    70343140,70343142,70343144,70343146,70343148,70343150,
    70343152,70343154,70343156,70343158,70343160,70343162,
    70343164,70343166,70343168,70343170,70343172,70343174,
    70343176,70343178,70343180,70343182,70343184,70343186,
    70343188,70343190,70343192,70343194,70343196,70343198,
    70343200,70343202,70343204,70343206,70343208,70343210,
    70343212,70343214,70343216,70343218,70343220,70343222,
    70343224
]

results = []

for match_id in MATCH_IDS:
    try:
        url = f"https://site.web.api.espn.com/apis/v2/sports/cricket/ipl/scoreboard?event={match_id}"
        r = requests.get(url, timeout=10)
        data = r.json()

        event = data.get("events", [])[0]
        comp = event["competitions"][0]
        teams = comp["competitors"]

        home = teams[0]
        away = teams[1]

        match = {
            "match_id": match_id,
            "date": event.get("date", ""),
            "home_team": home["team"]["displayName"],
            "away_team": away["team"]["displayName"],
            "home_score": home.get("score", ""),
            "away_score": away.get("score", ""),
            "status": comp["status"]["type"]["description"]
        }

        results.append(match)
        print("✔", match_id)

    except Exception as e:
        print("❌ failed:", match_id)

# save
with open(OUTPUT, "w") as f:
    json.dump(results, f, indent=2)

print("DONE:", len(results), "matches")
