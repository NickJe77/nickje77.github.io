import requests, os, sys, json

season = sys.argv[1]

print("Fetching ESPN schedule:", season)

url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?seasontype=2&year={season}"

res = requests.get(url)
data = res.json()

games = []

for event in data.get("events", []):

    game_id = event.get("id")

    competitions = event.get("competitions", [])[0]

    competitors = competitions.get("competitors", [])

    home = [c for c in competitors if c.get("homeAway") == "home"][0]
    away = [c for c in competitors if c.get("homeAway") == "away"][0]

    games.append({
        "game_id": game_id,
        "home_team": home["team"]["displayName"],
        "away_team": away["team"]["displayName"],
        "home_score": home.get("score"),
        "away_score": away.get("score"),
        "status": competitions.get("status", {}).get("type", {}).get("description")
    })

print("Games found:", len(games))

os.makedirs("docs/data/nfl/raw", exist_ok=True)

with open(f"docs/data/nfl/raw/{season}_games.json","w") as f:
    json.dump(games, f)
