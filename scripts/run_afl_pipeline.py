import json
import re
import time
from pathlib import Path
from collections import defaultdict

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

print("AFL PIPELINE (PLAYWRIGHT STEALTH VERSION)")

BASE = "https://www.footywire.com"
SEASON = 2026

DATA_DIR = Path("docs/data/afl")
OUTPUT = DATA_DIR / f"afl_{SEASON}.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)


# -------------------------------
# BROWSER SETUP (REALISTIC)
# -------------------------------
def launch_browser(p):
    browser = p.chromium.launch(headless=True)

    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
        viewport={"width": 1280, "height": 800},
        locale="en-AU"
    )

    page = context.new_page()
    return browser, page


# -------------------------------
# FETCH WITH WAIT
# -------------------------------
def fetch(page, url):
    try:
        page.goto(url, timeout=60000)

        # 🔥 WAIT FOR TABLE (CRITICAL)
        page.wait_for_selector("table", timeout=10000)

        # 🔥 SCROLL (triggers lazy load)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1)

        return page.content()

    except Exception as e:
        print("FAILED:", url)
        return None


# -------------------------------
# HELPERS
# -------------------------------
def clean(text):
    return re.sub(r"\s+", " ", (text or "")).strip()


def to_int(text):
    try:
        return int(clean(text))
    except:
        return 0


# -------------------------------
# GET LINKS
# -------------------------------
def get_links(page):
    links = set()

    for rnd in range(0, 31):
        url = f"{BASE}/afl/footy/ft_match_list?year={SEASON}&round={rnd}"
        print("Round:", rnd)

        html = fetch(page, url)
        if not html:
            continue

        soup = BeautifulSoup(html, "html.parser")

        for a in soup.find_all("a", href=True):
            href = a["href"]

            if "ft_match_statistics" not in href:
                continue

            if href.startswith("/"):
                href = BASE + href

            links.add(href)

        time.sleep(1)

    print("MATCH LINKS:", len(links))
    return sorted(links)


# -------------------------------
# PARSE MATCH
# -------------------------------
def parse_match(page, url, match_counter):
    html = fetch(page, url)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")

    rows = soup.find_all("tr")

    data = []
    current_team = None

    for tr in rows:
        txt = clean(tr.get_text(" ", strip=True))

        m = re.match(r"^(.*?) Match Statistics", txt)
        if m:
            current_team = clean(m.group(1))
            continue

        cols = tr.find_all("td", recursive=False)
        if len(cols) < 18:
            continue

        link = cols[0].find("a")
        if not link:
            continue

        name = clean(link.text)

        row = {
            "match_id": f"{SEASON}_{match_counter:04d}",
            "player": name,
            "team": current_team,
            "K": to_int(cols[1].text),
            "HB": to_int(cols[2].text),
            "D": to_int(cols[3].text),
        }

        data.append(row)

    print(f"Match {match_counter}: {len(data)} rows")
    return data


# -------------------------------
# MAIN
# -------------------------------
def main():
    with sync_playwright() as p:
        browser, page = launch_browser(p)

        links = get_links(page)

        all_rows = []
        for i, link in enumerate(links, 1):
            print("Match:", i)
            rows = parse_match(page, link, i)
            all_rows.extend(rows)

        browser.close()

    print("TOTAL ROWS:", len(all_rows))

    if len(all_rows) < 100:
        print("❌ STILL BLOCKED")
        return

    OUTPUT.write_text(json.dumps(all_rows, indent=2))
    print("✅ DATA SAVED")


if __name__ == "__main__":
    main()
