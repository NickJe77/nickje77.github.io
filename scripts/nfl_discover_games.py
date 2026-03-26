import requests, os, sys, json

season = sys.argv[1]

print("Fetching FULL ESPN season:", season)

games = []

# NFL weeks
for week in range(1, 19):

    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?seasontype=2&year={season}&week={week}"

    res = requests.get(url)

    if res.status_code != 200:
        continue

    data = res.json()

    for event in data.get("events", []):

        game_id = event.get("id")

        comp = event.get("competitions", [])[0]
        competitors = comp.get("competitors", [])

        home = [c for c in competitors if c["homeAway"] == "home"][0]
        away = [c for c in competitors if c["homeAway"] == "away"][0]

        games.append({
            "game_id": game_id,
            "home_team": home["team"]["displayName"],
            "away_team": away["team"]["displayName"],
            "home_score": home.get("score"),
            "away_score": away.get("score")
        })

print("Games found:", len(games))

# remove duplicates
seen = set()
unique = []

for g in games:
    if g["game_id"] not in seen:
        seen.add(g["game_id"])
        unique.append(g)

os.makedirs("docs/data/nfl/raw", exist_ok=True)

with open(f"docs/data/nfl/raw/{season}_games.json","w") as f:
    json.dump(unique, f)
