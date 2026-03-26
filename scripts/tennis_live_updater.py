import os
import json
import requests

OUTPUT_DIR = "docs/data/tennis/matches"

ATP_URL = "https://api.atptour.com/atpworldtour/tennis/scores/results"
WTA_URL = "https://api.wtatennis.com/tennis/scores/results"


def fetch(url):
    try:
        r = requests.get(url, timeout=20)
        if r.status_code == 200:
            return r.json()
    except:
        return None
    return None


def process_api(data, gender):
    matches = []

    if not data:
        return matches

    for event in data.get("events", []):
        for m in event.get("matches", []):

            try:
                matches.append({
                    "tournament": event.get("name"),
                    "surface": event.get("surface"),
                    "round": m.get("round"),
                    "player1": m.get("winner", {}).get("name"),
                    "player2": m.get("loser", {}).get("name"),
                    "score": m.get("score"),
                    "date": m.get("date"),
                    "gender": gender
                })
            except:
                continue

    return matches


def update_year(year, new_matches):

    path = f"{OUTPUT_DIR}/{year}.json"

    if os.path.exists(path):
        existing = json.load(open(path))
    else:
        existing = []

    # avoid duplicates
    existing_keys = set(
        (m["player1"], m["player2"], m["date"])
        for m in existing
    )

    for m in new_matches:
        key = (m["player1"], m["player2"], m["date"])
        if key not in existing_keys:
            existing.append(m)

    json.dump(existing, open(path, "w"), indent=2)
    print(f"{year} updated ({len(existing)})")


def main():

    print("Fetching ATP...")
    atp = fetch(ATP_URL)

    print("Fetching WTA...")
    wta = fetch(WTA_URL)

    matches = []
    matches += process_api(atp, "M")
    matches += process_api(wta, "W")

    # split by year
    by_year = {}

    for m in matches:
        year = str(m["date"])[:4]
        if year not in by_year:
            by_year[year] = []
        by_year[year].append(m)

    for year, mlist in by_year.items():
        update_year(year, mlist)


if __name__ == "__main__":
    main()
