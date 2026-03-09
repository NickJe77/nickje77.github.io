import requests
import json

print("Downloading schedule...")

url = "https://cdn.nba.com/static/json/staticData/scheduleLeagueV2.json"

r = requests.get(url)

print("Status:", r.status_code)

data = r.json()

print("\nTop level keys:")
print(list(data.keys()))

league = data.get("leagueSchedule", {})

print("\nleagueSchedule keys:")
print(list(league.keys()))

dates = league.get("gameDates", [])

print("\nTotal gameDates:", len(dates))

if len(dates) > 0:

    first = dates[0]

    print("\nKeys inside gameDates item:")
    print(list(first.keys()))

    games = first.get("games", [])

    print("\nGames in first date:", len(games))

    if len(games) > 0:

        print("\nKeys inside first game:")
        print(list(games[0].keys()))
