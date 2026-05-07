import os
import json
from collections import defaultdict

BASE = "docs/data/baseball"
SEASONS_DIR = f"{BASE}/seasons"
BOX_DIR = f"{BASE}/boxscores"
OUT_DIR = f"{BASE}/players"

os.makedirs(OUT_DIR, exist_ok=True)

players = defaultdict(lambda: {
    "name":"",
    "games":[]
})

season_files = sorted([
    f for f in os.listdir(SEASONS_DIR)
    if f.endswith(".json")
])

for sf in season_files:

    season = sf.replace(".json","")

    season_path = f"{SEASONS_DIR}/{sf}"

    try:
        with open(season_path,"r",encoding="utf-8") as f:
            games = json.load(f)
    except:
        continue

    for g in games:

        file_name = (
            g.get("game_file") or
            g.get("filename") or
            g.get("file")
        )

        if not file_name:
            continue

        box_path = f"{BOX_DIR}/{season}/{file_name}"

        if not os.path.exists(box_path):
            continue

        try:
            with open(box_path,"r",encoding="utf-8") as f:
                box = json.load(f)
        except:
            continue

        date = box.get("date","")

        home_code = (
            box.get("home_code") or
            g.get("home_code","")
        )

        away_code = (
            box.get("away_code") or
            g.get("away_code","")
        )

        home_list = (
            box.get("batters_home") or
            box.get("batting_home") or
            []
        )

        away_list = (
            box.get("batters_away") or
            box.get("batting_away") or
            []
        )

        def process_player(p,is_home):

            name = (
                p.get("name") or
                p.get("fullName") or
                p.get("player") or
                ""
            ).strip()

            if not name:
                return

            key = name.lower()

            ab = int(
                p.get("AB") or
                p.get("ab") or
                p.get("atBats") or
                0
            )

            hits = int(
                p.get("H") or
                p.get("h") or
                p.get("hits") or
                0
            )

            hr = int(
                p.get("HR") or
                p.get("hr") or
                p.get("homeRuns") or
                0
            )

            players[key]["name"] = name

            players[key]["games"].append({
                "date":date,
                "team":home_code if is_home else away_code,
                "opponent":away_code if is_home else home_code,
                "AB":ab,
                "H":hits,
                "HR":hr
            })

        for p in home_list:
            process_player(p,True)

        for p in away_list:
            process_player(p,False)

print("Saving player files...")

for key,data in players.items():

    slug = (
        key
        .replace(" ","-")
        .replace(".","")
        .replace("'","")
    )

    out_path = f"{OUT_DIR}/{slug}.json"

    with open(out_path,"w",encoding="utf-8") as f:
        json.dump(data,f,indent=2)

print(f"Built {len(players)} player files")
