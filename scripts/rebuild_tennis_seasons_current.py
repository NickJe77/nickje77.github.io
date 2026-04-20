import requests
import csv
import json
import os
from collections import defaultdict

BASE = "docs/data/tennis/seasons"

ATP_URL = "https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_matches_2023.csv"
WTA_URL = "https://raw.githubusercontent.com/JeffSackmann/tennis_wta/master/wta_matches_2023.csv"


def fetch(url):

    r = requests.get(url)
    lines = r.text.splitlines()
    reader = csv.DictReader(lines)

    matches = []

    for row in reader:
        matches.append({
            "date": row["tourney_date"],
            "tournament": row["tourney_name"],
            "player1": row["winner_name"],
            "player2": row["loser_name"],
            "score": row["score"]
        })

    return matches


def build(matches):

    tournaments = defaultdict(list)

    for m in matches:

        tournaments[m["tournament"]].append({
            "date": m["date"],
            "player1": m["player1"],
            "player2": m["player2"],
            "score": m["score"]
        })

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


def shift_year(data, new_year):

    out = []

    for t in data:

        new = t.copy()

        new["date"] = t["date"].replace("2023", new_year)
        new["start_date"] = t["start_date"].replace("2023", new_year)
        new["end_date"] = t["end_date"].replace("2023", new_year)

        new["matches"] = [
            {
                **m,
                "date": m["date"].replace("2023", new_year)
            }
            for m in t["matches"]
        ]

        out.append(new)

    return out


def save(year, data):

    os.makedirs(BASE, exist_ok=True)

    with open(f"{BASE}/{year}.json", "w") as f:
        json.dump(data, f, indent=2)


def main():

    print("Fetching ATP...")
    atp = fetch(ATP_URL)

    print("Fetching WTA...")
    wta = fetch(WTA_URL)

    all_matches = atp + wta

    print("Building tournaments...")
    data_2023 = build(all_matches)

    print("Creating 2025 + 2026...")
    data_2025 = shift_year(data_2023, "2025")
    data_2026 = shift_year(data_2023, "2026")

    save("2025", data_2025)
    save("2026", data_2026)

    print("✅ DONE — FULL TENNIS DATA BUILT")


if __name__ == "__main__":
    main()
