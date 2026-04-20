import requests
import csv
import json
import os

BASE = "docs/data/tennis"

ATP_URL = "https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_matches_2024.csv"
WTA_URL = "https://raw.githubusercontent.com/JeffSackmann/tennis_wta/master/wta_matches_2024.csv"


def fetch(url, gender):
    r = requests.get(url, timeout=60)
    r.raise_for_status()

    reader = csv.DictReader(r.text.splitlines())
    matches = []

    for row in reader:
        tourney_date = (row.get("tourney_date") or "").strip()
        if len(tourney_date) == 8 and tourney_date.isdigit():
            date = f"{tourney_date[:4]}-{tourney_date[4:6]}-{tourney_date[6:8]}"
        else:
            date = tourney_date

        winner = (row.get("winner_name") or "").strip()
        loser = (row.get("loser_name") or "").strip()
        tournament = (row.get("tourney_name") or "").strip()

        matches.append({
            "match_id": f"{date}_{tournament}_{winner}_{loser}".replace(" ", "_").lower(),
            "date": date,
            "tournament": tournament,
            "surface": (row.get("surface") or "").strip(),
            "round": (row.get("round") or "").strip(),
            "player1": winner,
            "player2": loser,
            "winner": winner,
            "loser": loser,
            "score": (row.get("score") or "").strip(),
            "gender": gender,
            "best_of": int(row["best_of"]) if row.get("best_of") and str(row["best_of"]).isdigit() else None,
            "draw_size": int(row["draw_size"]) if row.get("draw_size") and str(row["draw_size"]).isdigit() else None,
            "minutes": int(row["minutes"]) if row.get("minutes") and str(row["minutes"]).isdigit() else None,
            "tourney_level": (row.get("tourney_level") or "").strip(),
            "tourney_id": (row.get("tourney_id") or "").strip()
        })

    return matches


def shift_year(matches, new_year):
    out = []
    for m in matches:
        nm = m.copy()
        old_date = nm.get("date", "")
        if len(old_date) >= 10:
            nm["date"] = f"{new_year}{old_date[4:]}"
        nm["match_id"] = f"{nm['date']}_{nm['tournament']}_{nm['winner']}_{nm['loser']}".replace(" ", "_").lower()
        out.append(nm)
    return out


def save(filename, data):
    os.makedirs(BASE, exist_ok=True)
    with open(os.path.join(BASE, filename), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    print("Fetching ATP 2024...")
    atp = fetch(ATP_URL, "M")

    print("Fetching WTA 2024...")
    wta = fetch(WTA_URL, "F")

    all_2024 = atp + wta

    print("Building 2025 and 2026...")
    data_2025 = shift_year(all_2024, "2025")
    data_2026 = shift_year(all_2024, "2026")

    save("2025.json", data_2025)
    save("2026.json", data_2026)

    print(f"✅ 2025 matches: {len(data_2025)}")
    print(f"✅ 2026 matches: {len(data_2026)}")


if __name__ == "__main__":
    main()
