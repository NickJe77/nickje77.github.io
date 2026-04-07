from playwright.sync_api import sync_playwright
import json
from pathlib import Path

print("LIV SCRAPER (API INTERCEPT)")

OUTPUT = Path("docs/data/golf")
OUTPUT.mkdir(parents=True, exist_ok=True)

OUT_FILE = OUTPUT / "liv_winners.json"

YEARS = [2022, 2023, 2024, 2025, 2026]

rows = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    captured = []

    def handle_response(response):
        url = response.url

        # 🔥 capture LIV API responses
        if "schedule" in url or "event" in url or "api" in url:
            try:
                data = response.json()
                captured.append(data)
            except:
                pass

    page.on("response", handle_response)

    for year in YEARS:
        print("YEAR", year)

        url = f"https://www.livgolf.com/schedule?season={year}"
        page.goto(url, wait_until="domcontentloaded", timeout=120000)

        page.wait_for_timeout(8000)

    browser.close()


# ---------------------------
# PARSE CAPTURED DATA
# ---------------------------
for block in captured:
    try:
        # adapt depending on API structure
        if isinstance(block, dict):
            for key in block:
                if isinstance(block[key], list):
                    for item in block[key]:

                        event = item.get("name") or item.get("eventName") or ""
                        winner = ""

                        # try to extract winner
                        if "winner" in item:
                            winner = item["winner"]

                        rows.append({
                            "tour": "liv",
                            "year": item.get("year", ""),
                            "date": "",
                            "event": event,
                            "winner": winner,
                            "score": "",
                            "venue": "",
                            "country": "",
                            "url": ""
                        })

    except:
        continue


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
