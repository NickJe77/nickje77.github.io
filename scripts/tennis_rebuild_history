import requests
import json
from pathlib import Path
import csv
from io import StringIO

print("REBUILDING TENNIS HISTORY (1968–2024)")

BASE = Path("docs/data/tennis")
MATCH_DIR = BASE / "matches"
MATCH_DIR.mkdir(parents=True, exist_ok=True)

# Sackmann dataset (reliable historical source)
URL = "https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_matches_{}.csv"

all_data = {}

for year in range(1968, 2025):
    print(f"Fetching {year}...")

    try:
        r = requests.get(URL.format(year), timeout=30)
        if r.status_code != 200:
            print(f"Missing {year}")
            continue
    except:
        print(f"Failed {year}")
        continue

    f = StringIO(r.text)
    reader = csv.DictReader(f)

    matches = []

    for row in reader:
        try:
            matches.append({
                "tournament": row["tourney_name"],
                "surface": row["surface"] or "Hard",
                "round": row["round"],
                "player1": row["winner_name"],
                "player2": row["loser_name"],
                "score": row["score"],
                "date": row["tourney_date"],
                "gender": "M"
            })
        except:
            continue

    if matches:
        with open(MATCH_DIR / f"{year}.json", "w") as f:
            json.dump(matches, f, indent=2)

        print(f"Saved {year}: {len(matches)} matches")
