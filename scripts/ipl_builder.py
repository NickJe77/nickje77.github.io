import requests
import json
import os
from datetime import datetime

BASE = "https://site.api.espn.com/apis/site/v2/sports/cricket/ipl/scoreboard"

SEASON = 2026

OUTPUT_MATCH_DIR = "docs/data/ipl/matches/2026"
OUTPUT_SEASON_FILE = "docs/data/ipl/ipl_2026.json"

os.makedirs(OUTPUT_MATCH_DIR, exist_ok=True)

def get_matches():
    matches = []

    for page in range(1, 20):
        url = f"{BASE}?dates={SEASON}&page={page}"
        r = requests.get(url)

        if r.status_code != 200:
            continue

        data = r.json()

        events = data.get("events", [])
        if not events:
            break

        for event in events:
            comp = event["competitions"][0]

            match_id = event["id"]
            date = event["date"]

            teams = comp["competitors"]

            home = next(t for t in teams if t["homeAway"] == "home")
            away = next(t for t in teams if t["homeAway"] == "away")

            matches.append({
                "match_id": match_id,
                "date": date,
                "home_team": home["team"]["displayName"],
                "away_team": away["team"]["displayName"],
                "home_score": home.get("score", "0"),
                "away_score": away.get("score", "0"),
                "status": comp["status"]["type"]["description"]
            })

    return matches


def save_match(match):
    url = f"https://site.api.espn.com/apis/site/v2/sports/cricket/ipl/summary?event={match['match_id']}"
    r = requests.get(url)

    if r.status_code != 200:
        return

    data = r.json()

    path = f"{OUTPUT_MATCH_DIR}/{match['match_id']}.json"

    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def main():
    matches = get_matches()

    results = []

    for m in matches:
        save_match(m)

        results.append({
            "match_id": m["match_id"],
            "date": m["date"],
            "home_team": m["home_team"],
            "away_team": m["away_team"],
            "home_score": m["home_score"],
            "away_score": m["away_score"],
            "status": m["status"],
            "file": f"{m['match_id']}.json"
        })

    with open(OUTPUT_SEASON_FILE, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Saved {len(results)} matches")


if __name__ == "__main__":
    main()
