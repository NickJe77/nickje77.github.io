import requests
import json
from datetime import datetime
from pathlib import Path

print("TENNIS SCRAPER (WORKING SOURCE)")

OUTPUT_DIR = Path("docs/data/tennis/seasons")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

START_YEAR = 2025
END_YEAR = datetime.utcnow().year


# -----------------------------------
# FETCH MATCHES (ATP STYLE DATA)
# -----------------------------------
def fetch_year(year):
    print(f"\nFetching {year}...")

    matches = []

    # Example working endpoint (stable public dataset style)
    url = f"https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_matches_{year}.csv"

    try:
        r = requests.get(url, timeout=30)

        if r.status_code != 200:
            print(f"FAILED {year}")
            return []

        lines = r.text.splitlines()

        headers = lines[0].split(",")

        for line in lines[1:]:
            parts = line.split(",")

            try:
                date = parts[5]
                player1 = parts[10]
                player2 = parts[18]
                score = parts[27]
                tournament = parts[1]

                matches.append({
                    "date": date,
                    "tournament": tournament,
                    "player1": player1,
                    "player2": player2,
                    "score": score
                })

            except:
                continue

        print(f"{year} matches: {len(matches)}")
        return matches

    except Exception as e:
        print("ERROR:", e)
        return []


# -----------------------------------
# RUN
# -----------------------------------
total = 0

for y in range(START_YEAR, END_YEAR + 1):
    data = fetch_year(y)

    if data:
        with open(OUTPUT_DIR / f"{y}.json", "w") as f:
            json.dump(data, f, indent=2)

        total += len(data)

print(f"\nDONE. TOTAL MATCHES: {total}")
