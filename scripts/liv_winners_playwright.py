from playwright.sync_api import sync_playwright
import json
from pathlib import Path
import time

print("LIV SCRAPER (PLAYWRIGHT FIXED)")

OUTPUT = Path("docs/data/golf")
OUTPUT.mkdir(parents=True, exist_ok=True)

OUT_FILE = OUTPUT / "liv_winners.json"

YEARS = [2022, 2023, 2024, 2025, 2026]

rows = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    )

    page = context.new_page()

    for year in YEARS:
        print(f"YEAR {year}")

        url = f"https://www.livgolf.com/schedule?season={year}"

        try:
            page.goto(url, timeout=120000, wait_until="domcontentloaded")

            # wait for page to render something useful
            page.wait_for_timeout(8000)

            # grab page text (fallback method)
            content = page.content()

            # VERY IMPORTANT: fallback extraction
            blocks = page.query_selector_all("div")

            print("  elements:", len(blocks))

            for b in blocks:
                try:
                    text = b.inner_text()

                    if "LIV Golf" in text and len(text) < 200:
                        lines = text.split("\n")

                        event = lines[0].strip()
                        winner = ""

                        for i, l in enumerate(lines):
                            if "Winner" in l and i + 1 < len(lines):
                                winner = lines[i + 1].strip()

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

        except Exception as e:
            print("FAILED YEAR:", year, e)

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
