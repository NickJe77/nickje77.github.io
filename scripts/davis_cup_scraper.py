from playwright.sync_api import sync_playwright
import json
from pathlib import Path

print("🏆 Davis Cup scraper (official site)")

BASE = "https://www.daviscup.com"
YEAR = "2025"

SECTIONS = [
    f"{BASE}/en/draws-results/{YEAR}/qualifiers",
    f"{BASE}/en/draws-results/{YEAR}/world-group-i",
    f"{BASE}/en/draws-results/{YEAR}/world-group-ii",
    f"{BASE}/en/draws-results/{YEAR}/finals",
]

matches = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    tie_links = set()

    # -------------------------
    # GET ALL TIES
    # -------------------------
    for section in SECTIONS:
        print("→ section:", section)
        page.goto(section, timeout=60000)

        links = page.eval_on_selector_all(
            "a",
            "els => els.map(e => e.href)"
        )

        for link in links:
            if f"/{YEAR}/" in link and "-" in link and "vs" in link:
                tie_links.add(link)

    print("Ties found:", len(tie_links))

    # -------------------------
    # SCRAPE EACH TIE
    # -------------------------
    for link in tie_links:
        print("→ tie:", link)

        page.goto(link, timeout=60000)

        rows = page.query_selector_all("tr")

        for row in rows:
            text = row.inner_text()

            if " def " not in text:
                continue

            if "/" in text:
                match_type = "Doubles"
            else:
                match_type = "Singles"

            matches.append({
                "text": text.strip(),
                "match_type": match_type
            })

    browser.close()

print("Matches found:", len(matches))

OUT = Path(f"docs/data/tennis/davis_cup/{YEAR}.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

with open(OUT, "w") as f:
    json.dump(matches, f, indent=2)

print("✅ Saved:", len(matches))
