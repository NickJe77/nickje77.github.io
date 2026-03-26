import os
import json
import time
import requests
from bs4 import BeautifulSoup

BASE_DIR = "docs/data/tennis/events"
OUTPUT_DIR = "docs/data/tennis/matches"

os.makedirs(OUTPUT_DIR, exist_ok=True)

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0"
})


# -----------------------------------
# SEARCH TOURNAMENT (Tennis Abstract)
# -----------------------------------
def get_tournament_url(name, year):
    query = f"{name} {year} tennis abstract"
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"

    try:
        r = session.get(url)
        soup = BeautifulSoup(r.text, "html.parser")

        for a in soup.select("a"):
            href = a.get("href", "")
            if "tennisabstract.com" in href:
                return href.split("/url?q=")[-1].split("&")[0]
    except:
        return None

    return None


# -----------------------------------
# PARSE TOURNAMENT PAGE
# -----------------------------------
def parse_tournament(url):
    soup = None
    try:
        r = session.get(url, timeout=20)
        if r.status_code != 200:
            return []
        soup = BeautifulSoup(r.text, "html.parser")
    except:
        return []

    matches = []

    try:
        rows = soup.select("table tr")

        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 4:
                continue

            p1 = cols[1].get_text(strip=True)
            p2 = cols[2].get_text(strip=True)
            score = cols[3].get_text(strip=True)

            matches.append({
                "player1": p1,
                "player2": p2,
                "score": score,
                "winner": p1  # basic assumption
            })
    except:
        pass

    return matches


# -----------------------------------
# PROCESS YEAR FILE
# -----------------------------------
def process_year(file):
    year = file.replace(".json", "")
    print(f"\nYEAR {year}")

    tournaments = json.load(open(os.path.join(BASE_DIR, file)))

    year_data = []

    for t in tournaments:
        name = t.get("name")
        print(f"  Tournament: {name}")

        url = get_tournament_url(name, year)

        if not url:
            print("   ❌ no url")
            continue

        matches = parse_tournament(url)

        if not matches:
            print("   ❌ no matches")
            continue

        year_data.append({
            "tournament": name,
            "matches": matches
        })

        time.sleep(2)

    json.dump(
        year_data,
        open(os.path.join(OUTPUT_DIR, f"{year}.json"), "w"),
        indent=2
    )


# -----------------------------------
# MAIN
# -----------------------------------
def main():
    for file in sorted(os.listdir(BASE_DIR)):
        if not file.endswith(".json"):
            continue

        year = int(file.replace(".json", ""))

        if year < 1968:
            continue

        process_year(file)


if __name__ == "__main__":
    main()
