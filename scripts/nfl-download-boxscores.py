import json, os, time, sys, requests
from bs4 import BeautifulSoup

season = sys.argv[1]

games = json.load(open(f"docs/data/nfl/raw/{season}_games.json"))

OUT = f"docs/data/nfl/games/{season}"
os.makedirs(OUT, exist_ok=True)

for g in games:

    gid = g["game_id"]
    path = f"{OUT}/{gid}.json"

    if os.path.exists(path):
        print("Skipping:", gid)
        continue

    print("Scraping:", gid)

    try:
        r = requests.get(g["url"], headers={"User-Agent":"Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")

        teams = [t.text for t in soup.select("div.scorebox strong a")]
        scores = [int(s.text) for s in soup.select("div.scorebox div.score")]

        game_data = {
            "game_id": gid,
            "home_team": teams[1],
            "away_team": teams[0],
            "home_score": scores[1],
            "away_score": scores[0],
            "players": []
        }

        tables = soup.select("table")

        for table in tables:
            table_id = table.get("id", "")

            if any(x in table_id for x in ["passing", "rushing", "receiving"]):

                for row in table.select("tbody tr"):
                    cols = row.find_all("td")
                    if not cols:
                        continue

                    player_cell = row.find("th")
                    if not player_cell:
                        continue

                    player_name = player_cell.text.strip()

                    stats = {}
                    for td in cols:
                        stat = td.get("data-stat")
                        val = td.text.strip()
                        stats[stat] = val

                    game_data["players"].append({
                        "name": player_name,
                        "stats": stats
                    })

        with open(path, "w") as f:
            json.dump(game_data, f)

        time.sleep(2)

    except Exception as e:
        print("FAILED:", gid, e)
