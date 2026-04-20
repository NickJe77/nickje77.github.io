import json
import os
from collections import defaultdict

MATCH_FILE = "docs/data/tennis/full_match_database.json"
OUT = "docs/data/tennis/seasons"

def load(path):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f)

def save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def build(matches, year):

    tournaments = defaultdict(list)

    for m in matches:

        if not m["date"].startswith(year):
            continue

        tournaments[m["tournament"]].append(m)

    output = []

    for name, games in tournaments.items():

        dates = sorted([g["date"] for g in games])

        output.append({
            "tournament": name,
            "surface": "",
            "location": "",
            "tour": "",
            "start_date": dates[0],
            "end_date": dates[-1],
            "date": dates[0],
            "matches": games
        })

    output.sort(key=lambda x: x["date"])

    return output


def main():

    matches = load(MATCH_FILE)

    for year in ["2025", "2026"]:
        data = build(matches, year)
        save(f"{OUT}/{year}.json", data)
        print(year, len(data))


if __name__ == "__main__":
    main()
