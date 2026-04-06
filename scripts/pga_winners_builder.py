import requests
import json
from pathlib import Path
from datetime import datetime
import time
from bs4 import BeautifulSoup

print("PGA WINNERS BUILDER (WORKING VERSION)")

OUTPUT = Path("docs/data/golf")
OUTPUT.mkdir(parents=True, exist_ok=True)

OUT_FILE = OUTPUT / "pga_winners.json"

HEADERS = {"User-Agent": "Mozilla/5.0"}

CURRENT_YEAR = datetime.utcnow().year

YEARS = list(range(2015, CURRENT_YEAR + 1))  # safer range


def get_schedule(year):
    url = f"https://www.pgatour.com/schedule/{year}"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        return []

    soup = BeautifulSoup(r.text, "html.parser")

    events = []

    cards = soup.select("a.c-card__link")

    for c in cards:
        href = c.get("href", "")
        name_el = c.select_one(".c-card__title")
        date_el = c.select_one(".c-card__date")
        loc_el = c.select_one(".c-card__subtitle")

        if not href or not name_el:
            continue

        events.append({
            "url": "https://www.pgatour.com" + href,
            "event": name_el.text.strip(),
            "date": date_el.text.strip() if date_el else "",
            "location": loc_el.text.strip() if loc_el else ""
        })

    return events


def get_winner(event_url):
    try:
        r = requests.get(event_url, headers=HEADERS)
        if r.status_code != 200:
            return None, None

        soup = BeautifulSoup(r.text, "html.parser")

        # winner = first leaderboard row
        player = soup.select_one(".leaderboard__player-name")
        score = soup.select_one(".leaderboard__score")

        if not player:
            return None, None

        name = player.text.strip()
        score_val = score.text.strip() if score else ""

        return name, score_val

    except:
        return None, None


all_rows = []

for year in YEARS:
    print(f"YEAR {year}")

    events = get_schedule(year)

    for e in events:
        try:
            print("  ", e["event"])

            winner, score = get_winner(e["url"])

            if not winner:
                continue

            country = e["location"].split(",")[-1].strip() if e["location"] else ""

            row = {
                "tour": "pga",
                "year": year,
                "date": "",
                "event": e["event"],
                "winner": winner,
                "score": score,
                "venue": e["location"],
                "country": country,
                "url": e["url"]
            }

            all_rows.append(row)

            time.sleep(0.5)

        except Exception as err:
            print("error", err)
            continue


all_rows.sort(key=lambda x: x["year"], reverse=True)

with open(OUT_FILE, "w") as f:
    json.dump(all_rows, f, indent=2)

print("DONE:", len(all_rows))
