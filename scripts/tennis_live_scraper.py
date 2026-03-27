import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

OUTPUT = "docs/data/tennis/matches"
os.makedirs(OUTPUT, exist_ok=True)

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
# 🔥 LIVE MATCHES (WORKING SOURCE)
# =========================
def fetch_current_matches():
    url = "https://www.atptour.com/en/scores/current"

    print("Fetching current matches...")

    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")

    matches = []

    for match in soup.select(".scores-draw-entry-box"):
        try:
            players = match.select(".scores-draw-entry-box__name")

            if len(players) < 2:
                continue

            p1 = players[0].text.strip()
            p2 = players[1].text.strip()

            score = match.select_one(".scores-draw-entry-box__score")

            score_text = score.text.strip() if score else ""

            matches.append({
                "player1": p1,
                "player2": p2,
                "score": score_text,
                "date": datetime.now().strftime("%Y-%m-%d")
            })

        except:
            continue

    return matches


def run():
    year = datetime.now().year

    existing = load_existing(year)

    seen = {(m["player1"], m["player2"], m["score"]) for m in existing}

    new_matches = []

    matches = fetch_current_matches()

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
