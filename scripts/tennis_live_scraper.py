import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

OUTPUT = "docs/data/tennis/matches"
os.makedirs(OUTPUT, exist_ok=True)

CURRENT_YEAR = datetime.now().year
YEARS = list(range(2025, CURRENT_YEAR + 1))

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def load_existing(year):
    path = f"{OUTPUT}/{year}.json"
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return []


def save_year(year, data):
    with open(f"{OUTPUT}/{year}.json", "w") as f:
        json.dump(data, f, indent=2)


# =========================
# TENNIS ABSTRACT SCRAPER
# =========================
def fetch_year(year):
    url = f"https://www.tennisabstract.com/cgi-bin/ytdmatches.cgi?year={year}"

    print("Fetching:", url)

    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")

    matches = []

    table = soup.find("table")

    if not table:
        print("No table found")
        return matches

    rows = table.find_all("tr")[1:]

    for row in rows:
        cols = row.find_all("td")

        if len(cols) < 10:
            continue

        try:
            matches.append({
                "date": cols[0].text.strip(),
                "tournament": cols[1].text.strip(),
                "surface": cols[2].text.strip(),
                "round": cols[3].text.strip(),
                "player1": cols[4].text.strip(),
                "player2": cols[5].text.strip(),
                "score": cols[6].text.strip()
            })
        except:
            continue

    return matches


def run():
    for year in YEARS:
        print(f"\nYEAR: {year}")

        existing = load_existing(year)
        seen = {(m["player1"], m["player2"], m["score"]) for m in existing}

        new_matches = []

        matches = fetch_year(year)

        for m in matches:
            key = (m["player1"], m["player2"], m["score"])

            if key not in seen:
                new_matches.append(m)
                seen.add(key)

        all_matches = existing + new_matches

        save_year(year, all_matches)

        print(f"Saved {len(all_matches)} matches ({len(new_matches)} new)")


if __name__ == "__main__":
    run()
