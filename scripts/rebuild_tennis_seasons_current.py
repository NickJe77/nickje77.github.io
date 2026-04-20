import requests
import json
import os

BASE = "docs/data/tennis"
OUT = os.path.join(BASE, "full_match_database.json")

URL = "https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_matches_2025.csv"

def main():

    print("Downloading dataset...")

    r = requests.get(URL)
    lines = r.text.splitlines()

    headers = lines[0].split(",")
    matches = []

    for line in lines[1:]:

        parts = line.split(",")

        row = dict(zip(headers, parts))

        matches.append({
            "date": row.get("tourney_date",""),
            "tournament": row.get("tourney_name",""),
            "surface": row.get("surface",""),
            "winner": row.get("winner_name",""),
            "loser": row.get("loser_name","")
        })

    os.makedirs(BASE, exist_ok=True)

    with open(OUT, "w") as f:
        json.dump(matches, f)

    print("✅ Saved match database")


if __name__ == "__main__":
    main()
