import requests
from bs4 import BeautifulSoup
import json
import os
import time
from datetime import datetime

OUTPUT = "docs/data/tennis/matches"
os.makedirs(OUTPUT, exist_ok=True)

CURRENT_YEAR = datetime.now().year
YEARS = list(range(2025, CURRENT_YEAR + 1))

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


# =========================
# LOAD / SAVE
# =========================
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
# 🔥 FLASHSCORE SCRAPER
# =========================
def get_matches(year):
    url = f"https://www.flashscore.com/tennis/atp-singles-{year}/results/"

    print("Fetching:", url)

    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")

    matches = []

    rows = soup.select("div.event__match")

    for r in rows:
        try:
            p1 = r.select_one(".event__participant--home").text.strip()
            p2 = r.select_one(".event__participant--away").text.strip()

            s1 = r.select_one(".event__score--home").text.strip()
            s2 = r.select_one(".event__score--away").text.strip()

            score = f"{s1}-{s2}"

            matches.append({
                "player1": p1,
                "player2": p2,
                "score": score,
                "year": year
            })

        except:
            continue

    return matches


# =========================
# MAIN
# =========================
def run():
    for year in YEARS:
        print(f"\nYEAR: {year}")

        existing = load_existing(year)
        seen = {(m["player1"], m["player2"], m["score"]) for m in existing}

        new_matches = []

        matches = get_matches(year)

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
