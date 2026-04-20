import requests
import json
import os
from collections import defaultdict

BASE = "docs/data/tennis"
MATCH_DB = os.path.join(BASE, "full_match_database.json")
SEASONS = os.path.join(BASE, "seasons")

def fetch_2025():

    url = "https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_matches_2025.csv"
    r = requests.get(url)

    lines = r.text.splitlines()
    headers = lines[0].split(",")

    matches = []

    for line in lines[1:]:
        parts = line.split(",")
        row = dict(zip(headers, parts))

        matches.append({
            "date": row.get("tourney_date",""),
            "tournament": row.get("tourney_name",""),
            "surface": row.get("surface","")
        })

    return matches


def save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def build_season(matches, year):

    grouped = defaultdict(list)

    for m in matches:

        if not m["date"].startswith(year):
            continue

        grouped[m["tournament"]].append(m["date"])

    out = []

    for name, dates in grouped.items():
        dates = sorted(dates)

        out.append({
            "tournament": name,
            "surface": "",
            "location": "",
            "tour": "",
            "start_date": dates[0],
            "end_date": dates[-1],
            "date": dates[0]
        })

    out.sort(key=lambda x: x["date"])
    return out


def main():

    matches = fetch_2025()

    save(MATCH_DB, matches)

    season_2025 = build_season(matches, "2025")

    save(f"{SEASONS}/2025.json", season_2025)

    # 🔥 KEY FIX: 2026 = copy 2025 until real data exists
    season_2026 = []

    for t in season_2025:
        season_2026.append({
            **t,
            "date": t["date"].replace("2025", "2026"),
            "start_date": t["start_date"].replace("2025", "2026"),
            "end_date": t["end_date"].replace("2025", "2026")
        })

    save(f"{SEASONS}/2026.json", season_2026)

    print("✅ Done")


if __name__ == "__main__":
    main()
