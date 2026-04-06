import requests
import json
from pathlib import Path
from datetime import datetime
import time

print("PGA WINNERS BUILDER (ESPN VERSION)")

OUTPUT = Path("docs/data/golf")
OUTPUT.mkdir(parents=True, exist_ok=True)

OUT_FILE = OUTPUT / "pga_winners.json"

BASE = "https://site.api.espn.com/apis/site/v2/sports/golf/pga"

CURRENT_YEAR = datetime.utcnow().year
YEARS = list(range(2015, CURRENT_YEAR + 1))


def get_events(year):
    url = f"{BASE}/scoreboard?year={year}"
    r = requests.get(url)

    if r.status_code != 200:
        print("Failed ESPN", year)
        return []

    return r.json().get("events", [])


def extract_winner(event):
    try:
        competitions = event.get("competitions", [])
        if not competitions:
            return None, None

        competitors = competitions[0].get("competitors", [])
        if not competitors:
            return None, None

        # winner = lowest score
        winner = sorted(
            competitors,
            key=lambda x: int(x.get("score", 9999))
        )[0]

        name = winner.get("athlete", {}).get("displayName", "")
        score = winner.get("score", "")

        return name, score

    except:
        return None, None


all_rows = []

for year in YEARS:
    print(f"YEAR {year}")

    events = get_events(year)

    for e in events:
        try:
            name = e.get("name")
            date = e.get("date", "")[:10]

            winner, score = extract_winner(e)

            if not winner:
                continue

            venue = e.get("competitions", [{}])[0].get("venue", {}).get("fullName", "")
            country = e.get("competitions", [{}])[0].get("venue", {}).get("address", {}).get("country", "")

            row = {
                "tour": "pga",
                "year": year,
                "date": date,
                "event": name,
                "winner": winner,
                "score": score,
                "venue": venue,
                "country": country,
                "url": ""
            }

            all_rows.append(row)

            time.sleep(0.2)

        except Exception as err:
            print("Error:", err)
            continue


# sort newest first
all_rows.sort(key=lambda x: x.get("date", ""), reverse=True)

with open(OUT_FILE, "w") as f:
    json.dump(all_rows, f, indent=2)

print("DONE:", len(all_rows))
