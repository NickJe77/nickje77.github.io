import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import time
import re

print("LIV BUILDER (REAL SCRAPER)")

OUTPUT = Path("docs/data/golf")
OUTPUT.mkdir(parents=True, exist_ok=True)

OUT_FILE = OUTPUT / "liv_winners.json"

HEADERS = {"User-Agent": "Mozilla/5.0"}

YEARS = [2022, 2023, 2024, 2025, 2026]


def clean(text):
    return text.replace("\n", "").strip()


def normalize(name):
    name = re.sub(r"\(.*?\)", "", name)
    name = re.sub(r"\*", "", name)
    return name.strip()


def get_year_events(year):
    url = f"https://www.livgolf.com/schedule?season={year}"
    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:
        print("FAILED:", year)
        return []

    soup = BeautifulSoup(r.text, "html.parser")

    events = []

    cards = soup.find_all("div", class_="event-card")

    for c in cards:
        try:
            event = c.find("h3").text.strip()

            winner_tag = c.find("span", string=lambda x: x and "Winner" in x)

            winner = ""

            if winner_tag:
                winner = winner_tag.find_next("span").text.strip()

            events.append({
                "year": year,
                "event": event,
                "winner": normalize(winner)
            })

        except:
            continue

    return events


rows = []

for year in YEARS:
    print("YEAR", year)

    events = get_year_events(year)

    print("  found:", len(events))

    for e in events:
        rows.append({
            "tour": "liv",
            "year": e["year"],
            "date": "",
            "event": e["event"],
            "winner": e["winner"],
            "score": "",
            "venue": "",
            "country": "",
            "url": ""
        })

    time.sleep(1)


# remove duplicates
seen = set()
clean_rows = []

for r in rows:
    key = (r["event"], r["year"])
    if key not in seen:
        seen.add(key)
        clean_rows.append(r)

clean_rows.sort(key=lambda x: (x["year"], x["event"]), reverse=True)

with open(OUT_FILE, "w") as f:
    json.dump(clean_rows, f, indent=2)

print("DONE:", len(clean_rows))
