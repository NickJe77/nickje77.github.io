import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import time
import re

print("LIV BUILDER (FIXED)")

OUTPUT = Path("docs/data/golf")
OUTPUT.mkdir(parents=True, exist_ok=True)

OUT_FILE = OUTPUT / "liv_winners.json"

HEADERS = {"User-Agent": "Mozilla/5.0"}

START_YEAR = 2022
END_YEAR = 2026


def clean(text):
    return text.replace("\n", "").replace("\xa0", " ").strip()


def normalize_name(name):
    name = re.sub(r"\(.*?\)", "", name)
    name = re.sub(r"\*", "", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip()


def get_page(year):
    url = f"https://en.wikipedia.org/wiki/{year}_LIV_Golf_League"
    r = requests.get(url, headers=HEADERS, timeout=20)

    if r.status_code != 200:
        print("FAILED", year)
        return None

    return BeautifulSoup(r.text, "html.parser")


def parse_year(soup, year):
    results = []

    tables = soup.find_all("table", class_="wikitable")

    for table in tables:
        headers = [clean(th.text).lower() for th in table.find_all("th")]

        winner_idx = None
        event_idx = None

        for i, h in enumerate(headers):
            if "winner" in h or "individual champion" in h:
                winner_idx = i
            if "event" in h or "tournament" in h or "location" in h:
                event_idx = i

        if winner_idx is None or event_idx is None:
            continue

        for tr in table.find_all("tr")[1:]:
            cols = [clean(td.text) for td in tr.find_all(["td", "th"])]

            if len(cols) <= max(winner_idx, event_idx):
                continue

            winner = normalize_name(cols[winner_idx])
            event = cols[event_idx]

            if not winner or not event:
                continue

            if winner.replace(",", "").isdigit():
                continue

            if len(winner) < 3:
                continue

            results.append({
                "tour": "liv",
                "year": year,
                "date": "",
                "event": event,
                "winner": winner,
                "score": "",
                "venue": "",
                "country": "",
                "url": f"https://en.wikipedia.org/wiki/{year}_LIV_Golf_League"
            })

    return results


all_rows = []

for year in range(START_YEAR, END_YEAR + 1):
    print(f"YEAR {year}")

    soup = get_page(year)
    if not soup:
        continue

    rows = parse_year(soup, year)

    print("  rows:", len(rows))

    all_rows.extend(rows)

    time.sleep(0.3)


# remove duplicates
seen = set()
clean_rows = []

for r in all_rows:
    key = (r["event"], r["year"])
    if key not in seen:
        seen.add(key)
        clean_rows.append(r)

clean_rows.sort(key=lambda x: (x["year"], x["event"]), reverse=True)


with open(OUT_FILE, "w") as f:
    json.dump(clean_rows, f, indent=2)

print("DONE:", len(clean_rows))
