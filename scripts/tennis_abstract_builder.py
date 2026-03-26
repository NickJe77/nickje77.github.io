import os
import json
import time
import requests
from bs4 import BeautifulSoup

INPUT_DIR = "docs/data/tennis/events"
OUTPUT_DIR = "docs/data/tennis/matches"

os.makedirs(OUTPUT_DIR, exist_ok=True)

BASE_URL = "https://www.tennisabstract.com/cgi-bin/tourney.cgi?t="

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0"
})


# -----------------------------------
# FETCH TOURNAMENT
# -----------------------------------
def fetch_tournament(tournament_id):
    url = BASE_URL + tournament_id

    try:
        r = session.get(url, timeout=20)
        if r.status_code != 200:
            print(f"FAIL {url}")
            return None
        return BeautifulSoup(r.text, "html.parser")
    except:
        return None


# -----------------------------------
# PARSE MATCHES
# -----------------------------------
def parse_matches(soup):
    matches = []

    rows = soup.select("table tr")

    for row in rows:
        cols = row.find_all("td")

        if len(cols) < 4:
            continue

        try:
            round_name = cols[0].get_text(strip=True)
            p1 = cols[1].get_text(strip=True)
            p2 = cols[2].get_text(strip=True)
            score = cols[3].get_text(strip=True)

            if not p1 or not p2:
                continue

            matches.append({
                "round": round_name,
                "player1": p1,
                "player2": p2,
                "score": score,
                "winner": p1  # winner always first on this site
            })

        except:
            continue

    return matches


# -----------------------------------
# PROCESS YEAR
# -----------------------------------
def process_year(file):
    year = file.replace(".json", "")
    print(f"\nYEAR {year}")

    tournaments = json.load(open(os.path.join(INPUT_DIR, file)))
    year_output = []

    for t in tournaments:
        tid = t.get("tournament_id")
        name = t.get("name")

        if not tid:
            continue

        print(f"  {name} ({tid})")

        soup = fetch_tournament(tid)
        if not soup:
            continue

        matches = parse_matches(soup)

        if not matches:
            print("   ⚠ no matches found")
            continue

        year_output.append({
            "tournament_id": tid,
            "name": name,
            "surface": t.get("surface"),
            "date": t.get("date"),
            "matches": matches
        })

        time.sleep(1)

    json.dump(
        year_output,
        open(os.path.join(OUTPUT_DIR, f"{year}.json"), "w"),
        indent=2
    )


# -----------------------------------
# MAIN
# -----------------------------------
def main():
    for file in sorted(os.listdir(INPUT_DIR)):
        if not file.endswith(".json"):
            continue

        year = int(file.replace(".json", ""))

        if year < 1968:
            continue

        process_year(file)


if __name__ == "__main__":
    main()
