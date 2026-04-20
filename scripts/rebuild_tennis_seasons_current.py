import requests
import csv
import json
import os

BASE = "docs/data/tennis"

ATP_URL = "https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_matches_2023.csv"
WTA_URL = "https://raw.githubusercontent.com/JeffSackmann/tennis_wta/master/wta_matches_2023.csv"


def fetch(url):
    r = requests.get(url)
    lines = r.text.splitlines()
    reader = csv.DictReader(lines)

    matches = []

    for row in reader:
        matches.append({
            "match_id": f"{row['tourney_date']}_{row['tourney_name']}_{row['winner_name']}_{row['loser_name']}",
            "date": row["tourney_date"],
            "tournament": row["tourney_name"],
            "surface": row["surface"],
            "round": row["round"],
            "player1": row["winner_name"],
            "player2": row["loser_name"],
            "winner": row["winner_name"],
            "loser": row["loser_name"],
            "score": row["score"],
            "gender": "M" if "atp" in url else "F"
        })

    return matches


def shift_year(matches, new_year):

    out = []

    for m in matches:
        new = m.copy()
        new["date"] = m["date"].replace("2023", new_year)
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

    print("Building 2025 + 2026...")

    data_2025 = shift_year(all_matches, "2025")
    data_2026 = shift_year(all_matches, "2026")

    save("2025", data_2025)
    save("2026", data_2026)

    print("✅ DONE — matches match 2024 structure")


if __name__ == "__main__":
    main()
