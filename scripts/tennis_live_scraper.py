import requests
import os
import json
from datetime import datetime

OUTPUT = "docs/data/tennis/matches"
os.makedirs(OUTPUT, exist_ok=True)

CURRENT_YEAR = datetime.now().year
YEARS = list(range(2025, CURRENT_YEAR + 1))

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def load_existing(year):
    path = f"{OUTPUT}/{year}.json"
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return []


def save_year(year, data):
    with open(f"{OUTPUT}/{year}.json", "w") as f:
        json.dump(data, f, indent=2)


# =========================
# 🔥 REAL MATCH API
# =========================
def fetch_matches(year):
    print(f"Fetching {year} from UTS API")

    url = f"https://api.ultimatetennisstatistics.com/matches?season={year}"

    res = requests.get(url, headers=HEADERS)

    if res.status_code != 200:
        print("FAILED:", res.status_code)
        return []

    data = res.json()

    matches = []

    for m in data.get("data", []):
        try:
            matches.append({
                "player1": m["winner"]["name"],
                "player2": m["loser"]["name"],
                "score": m.get("score", ""),
                "date": m.get("date", ""),
                "tournament": m.get("tournament", {}).get("name", ""),
                "surface": m.get("tournament", {}).get("surface", ""),
                "round": m.get("round", "")
            })
        except:
            continue

    return matches


def run():
    for year in YEARS:
        print(f"\nYEAR: {year}")

        existing = load_existing(year)
        seen = {(m["player1"], m["player2"], m["score"]) for m in existing}

        new_matches = []

        matches = fetch_matches(year)

        for m in matches:
            key = (m["player1"], m["player2"], m["score"])
            if key not in seen:
                new_matches.append(m)
                seen.add(key)

        all_matches = existing + new_matches

        save_year(year, all_matches)

        print(f"Saved {len(all_matches)} matches ({len(new_matches)} new)")


if __name__ == "__main__":
    run()
