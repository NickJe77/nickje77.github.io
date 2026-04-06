import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import time

print("PGA FULL HISTORY BUILDER (1968+)")

OUTPUT = Path("docs/data/golf")
OUTPUT.mkdir(parents=True, exist_ok=True)

OUT_FILE = OUTPUT / "pga_winners.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

START_YEAR = 1968
END_YEAR = 2026


def get_season_page(year):
    url = f"https://en.wikipedia.org/wiki/{year}_PGA_Tour"
    r = requests.get(url, headers=HEADERS, timeout=20)

    if r.status_code != 200:
        print("Failed:", year)
        return None

    return BeautifulSoup(r.text, "html.parser")


def clean_text(text):
    return text.replace("\n", "").replace("\xa0", " ").strip()


def parse_table(soup, year):
    tables = soup.find_all("table", {"class": "wikitable"})
    results = []

    for table in tables:
        headers = [clean_text(th.text).lower() for th in table.find_all("th")]

        # Ensure this is a tournament results table
        if "winner" not in " ".join(headers):
            continue

        rows = table.find_all("tr")[1:]

        for row in rows:
            cols = [clean_text(c.text) for c in row.find_all(["td", "th"])]

            # skip bad rows
            if len(cols) < 4:
                continue

            try:
                event = cols[1]
                winner = cols[3]

                # skip empty / weird rows
                if not event or not winner:
                    continue

                # skip headers repeated inside tables
                if winner.lower() == "winner":
                    continue

                results.append({
                    "tour": "pga",
                    "year": year,
                    "date": "",
                    "event": event,
                    "winner": winner,
                    "score": "",
                    "venue": "",
                    "country": "",
                    "url": f"https://en.wikipedia.org/wiki/{year}_PGA_Tour"
                })

            except:
                continue

    return results


all_rows = []

for year in range(START_YEAR, END_YEAR + 1):
    print(f"YEAR {year}")

    soup = get_season_page(year)

    if not soup:
        continue

    rows = parse_table(soup, year)

    print("  found:", len(rows))

    all_rows.extend(rows)

    time.sleep(0.3)  # safe + faster


# ---------------------------
# REMOVE DUPLICATES
# ---------------------------
seen = set()
clean = []

for r in all_rows:
    key = (r["event"], r["year"])
    if key not in seen:
        seen.add(key)
        clean.append(r)


# ---------------------------
# SORT
# ---------------------------
clean.sort(key=lambda x: (x["year"], x["event"]), reverse=True)


# ---------------------------
# SAVE
# ---------------------------
with open(OUT_FILE, "w") as f:
    json.dump(clean, f, indent=2)

print("DONE:", len(clean))
