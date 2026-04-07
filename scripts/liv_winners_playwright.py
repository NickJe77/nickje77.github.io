from playwright.sync_api import sync_playwright
import json
from pathlib import Path

print("LIV SCRAPER (NEXT DATA FIX)")

OUTPUT = Path("docs/data/golf")
OUTPUT.mkdir(parents=True, exist_ok=True)

OUT_FILE = OUTPUT / "liv_winners.json"

YEARS = [2022, 2023, 2024, 2025, 2026]

rows = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    for year in YEARS:
        print("YEAR", year)

        url = f"https://www.livgolf.com/schedule?season={year}"
        page.goto(url, wait_until="domcontentloaded", timeout=120000)

        page.wait_for_timeout(5000)

        try:
            # 🔥 extract Next.js data
            data = page.evaluate("() => window.__NEXT_DATA__")

            # navigate structure (varies slightly)
            props = data.get("props", {})
            page_props = props.get("pageProps", {})

            # try common paths
            events = []

            for key in page_props:
                if isinstance(page_props[key], list):
                    events = page_props[key]

            print("  events:", len(events))

            for e in events:
                name = e.get("name") or e.get("eventName") or ""
                winner = ""

                # try winner fields
                if "winner" in e:
                    winner = e["winner"]

                rows.append({
                    "tour": "liv",
                    "year": year,
                    "date": "",
                    "event": name,
                    "winner": winner,
                    "score": "",
                    "venue": "",
                    "country": "",
                    "url": url
                })

        except Exception as e:
            print("FAILED:", e)

    browser.close()


# remove duplicates
seen = set()
clean = []

for r in rows:
    key = (r["event"], r["year"])
    if key not in seen and r["event"]:
        seen.add(key)
        clean.append(r)

clean.sort(key=lambda x: (x["year"], x["event"]), reverse=True)

with open(OUT_FILE, "w") as f:
    json.dump(clean, f, indent=2)

print("DONE:", len(clean))
