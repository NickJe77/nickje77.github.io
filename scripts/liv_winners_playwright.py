from playwright.sync_api import sync_playwright
import json
from pathlib import Path
import time

print("LIV SCRAPER (PLAYWRIGHT)")

OUTPUT = Path("docs/data/golf")
OUTPUT.mkdir(parents=True, exist_ok=True)

OUT_FILE = OUTPUT / "liv_winners.json"

YEARS = [2022, 2023, 2024, 2025, 2026]

rows = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    for year in YEARS:
        print(f"YEAR {year}")

        url = f"https://www.livgolf.com/schedule?season={year}"
        page.goto(url, timeout=60000)

        # wait for JS to load
        page.wait_for_timeout(5000)

        # get all event cards
        cards = page.query_selector_all("div[class*=event]")

        print("  cards found:", len(cards))

        for c in cards:
            try:
                text = c.inner_text()

                lines = text.split("\n")

                event = lines[0].strip()
                winner = ""

                # look for winner in text
                for line in lines:
                    if "Winner" in line:
                        idx = lines.index(line)
                        if idx + 1 < len(lines):
                            winner = lines[idx + 1].strip()

                rows.append({
                    "tour": "liv",
                    "year": year,
                    "date": "",
                    "event": event,
                    "winner": winner,
                    "score": "",
                    "venue": "",
                    "country": "",
                    "url": url
                })

            except:
                continue

        time.sleep(2)

    browser.close()


# remove duplicates
seen = set()
clean = []

for r in rows:
    key = (r["event"], r["year"])
    if key not in seen:
        seen.add(key)
        clean.append(r)

clean.sort(key=lambda x: (x["year"], x["event"]), reverse=True)

with open(OUT_FILE, "w") as f:
    json.dump(clean, f, indent=2)

print("DONE:", len(clean))
