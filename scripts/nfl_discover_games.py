import json, os, sys, requests, time

season = sys.argv[1]

games = json.load(open(f"docs/data/nfl/raw/{season}_games.json"))

OUT = f"docs/data/nfl/games/{season}"
os.makedirs(OUT, exist_ok=True)

for g in games:

    gid = g["game_id"]

    print("Fetching:", gid)

    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event={gid}"

        res = requests.get(url)

        if res.status_code != 200:
            print("SKIP (bad response):", gid)
            continue

        data = res.json()

        # 🔥 HANDLE MISSING BOXSCORE
        if "boxscore" not in data:
            print("SKIP (no boxscore):", gid)
            continue

        players = []

        for team in data.get("boxscore", {}).get("players", []):

            for stat_group in team.get("statistics", []):

                labels = stat_group.get("labels", [])

                for athlete in stat_group.get("athletes", []):

                    stats = dict(zip(labels, athlete.get("stats", [])))

                    players.append({
                        "name": athlete.get("athlete", {}).get("displayName"),
                        "stats": stats
                    })

        game_data = {
            "game_id": gid,
            "home_team": g.get("home_team"),
            "away_team": g.get("away_team"),
            "home_score": g.get("home_score"),
            "away_score": g.get("away_score"),
            "players": players
        }

        with open(f"{OUT}/{gid}.json", "w") as f:
            json.dump(game_data, f)

        time.sleep(1)

    except Exception as e:
        print("FAILED:", gid, e)
