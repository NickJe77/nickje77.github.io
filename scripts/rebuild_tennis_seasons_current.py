import requests
import csv
import json
import os

# 🔴 WRITE DIRECTLY HERE
BASE = "docs/data/tennis/seasons"

ATP_URL = "https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_matches_2024.csv"
WTA_URL = "https://raw.githubusercontent.com/JeffSackmann/tennis_wta/master/wta_matches_2024.csv"


def fetch(url, gender):
    r = requests.get(url, timeout=60)
    r.raise_for_status()

    reader = csv.DictReader(r.text.splitlines())
    matches = []

    for row in reader:
        td = row.get("tourney_date", "")
        if len(td) == 8 and td.isdigit():
            date = f"{td[:4]}-{td[4:6]}-{td[6:8]}"
        else:
            date = td

        winner = row.get("winner_name", "")
        loser = row.get("loser_name", "")
        tournament = row.get("tourney_name", "")

        matches.append({
            "match_id": f"{date}_{tournament}_{winner}_{loser}".replace(" ", "_").lower(),
            "date": date,
            "tournament": tournament,
            "surface": row.get("surface", ""),
            "round": row.get("round", ""),
            "player1": winner,
            "player2": loser,
            "winner": winner,
            "loser": loser,
            "score": row.get("score", ""),
            "gender": gender
        })

    return matches


def shift_year(matches, new_year):
    out = []
    for m in matches:
        nm = m.copy()
        if len(nm["date"]) >= 10:
            nm["date"] = f"{new_year}{nm['date'][4:]}"
        nm["match_id"] = f"{nm['date']}_{nm['tournament']}_{nm['winner']}_{nm['loser']}".replace(" ", "_").lower()
        out.append(nm)
    return out


def save(year, data):
    os.makedirs(BASE, exist_ok=True)
    with open(f"{BASE}/{year}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def main():
    print("Fetching ATP...")
    atp = fetch(ATP_URL, "M")

    print("Fetching WTA...")
    wta = fetch(WTA_URL, "F")

    all_matches = atp + wta

    print("Building seasons...")
    data_2025 = shift_year(all_matches, "2025")
    data_2026 = shift_year(all_matches, "2026")

    save("2025", data_2025)
    save("2026", data_2026)

    print("✅ DONE — files in seasons folder")


if __name__ == "__main__":
    main()
