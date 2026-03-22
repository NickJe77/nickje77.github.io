import json
import re
import time
from pathlib import Path
from collections import defaultdict

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

print("AFL PIPELINE (PLAYWRIGHT VERSION)")

BASE = "https://www.footywire.com"
SEASON = 2026

DATA_DIR = Path("docs/data/afl")
OUTPUT = DATA_DIR / f"afl_{SEASON}.json"
PLAYERS_DIR = DATA_DIR / "players"
PLAYERS_JSON = DATA_DIR / "players.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)
PLAYERS_DIR.mkdir(parents=True, exist_ok=True)


# -------------------------------
# BROWSER FETCH
# -------------------------------
def fetch(page, url):
    try:
        page.goto(url, timeout=60000)
        time.sleep(2)
        return page.content()
    except:
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


def get_round_label(soup):
    text = soup.get_text(" ", strip=True).lower()

    finals = [
        "grand final",
        "preliminary final",
        "semi final",
        "qualifying final",
        "elimination final"
    ]

    for f in finals:
        if f in text:
            return f.title()

    m = re.search(r"round\s+(\d+)", text)
    if m:
        return f"Round {int(m.group(1))}"

    return None


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

    title = soup.find("title")
    if not title:
        return []

    text = clean(title.text.replace("AFL Match Statistics :", ""))

    if " def " not in text:
        return []

    team_a, team_b = text.split(" def ", 1)
    team_b = team_b.split(" at ")[0]

    round_label = get_round_label(soup) or f"Round {match_counter}"
    match_id = f"{SEASON}_{match_counter:04d}"

    rows = soup.find_all("tr")

    current_team = None
    data = []

    for tr in rows:
        txt = clean(tr.get_text(" ", strip=True))

        m = re.match(r"^(.*?) Match Statistics", txt)
        if m:
            current_team = clean(m.group(1))
            continue

        if not current_team:
            continue

        cols = tr.find_all("td", recursive=False)
        if len(cols) < 18:
            continue

        link = cols[0].find("a")
        if not link:
            continue

        name = clean(link.text)
        opponent = team_b if current_team == team_a else team_a

        row = {
            "match_id": match_id,
            "player": name,
            "played_for": current_team,
            "played_against": opponent,
            "season": SEASON,
            "round": round_label,
            "K": to_int(cols[1].text),
            "HB": to_int(cols[2].text),
            "D": to_int(cols[3].text),
            "M": to_int(cols[4].text),
            "G": to_int(cols[5].text),
            "B": to_int(cols[6].text),
            "T": to_int(cols[7].text),
            "HO": to_int(cols[8].text),
            "GA": to_int(cols[9].text),
            "I50": to_int(cols[10].text),
            "CL": to_int(cols[11].text),
            "CG": to_int(cols[12].text),
            "R50": to_int(cols[13].text),
            "FF": to_int(cols[14].text),
            "FA": to_int(cols[15].text),
            "AF": to_int(cols[16].text),
            "SC": to_int(cols[17].text),
        }

        data.append(row)

    print(f"Match {match_counter}: {len(data)} rows")
    return data


# -------------------------------
# MAIN
# -------------------------------
def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        links = get_links(page)

        all_rows = []
        for i, link in enumerate(links, 1):
            print("Match:", i)
            rows = parse_match(page, link, i)
            all_rows.extend(rows)

        browser.close()

    print("TOTAL ROWS:", len(all_rows))

    if len(all_rows) < 1000:
        print("❌ STILL BLOCKED")
        return

    OUTPUT.write_text(json.dumps(all_rows, indent=2))
    print("✅ DATA SAVED")


if __name__ == "__main__":
    main()
