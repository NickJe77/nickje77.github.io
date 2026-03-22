import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

print("AFL PIPELINE (FRESH SAFE START)")

BASE = "https://www.footywire.com"
SEASON = 2026

DATA_DIR = Path("docs/data/afl")
OUTPUT = DATA_DIR / f"afl_{SEASON}.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-AU,en;q=0.9"
})


# -------------------------------
# HELPERS
# -------------------------------
def clean(x):
    return re.sub(r"\s+", " ", (x or "")).strip()


def to_int(x):
    try:
        return int(clean(x))
    except:
        return 0


def fetch(url):
    try:
        r = session.get(url, timeout=20)

        if r.status_code == 200 and "Match Statistics" in r.text:
            return r.text

    except:
        pass

    return None


# -------------------------------
# GET ONE ROUND ONLY
# -------------------------------
def get_links():
    # 🔥 START WITH ROUND 0 ONLY
    rnd = 0

    url = f"{BASE}/afl/footy/ft_match_list?year={SEASON}&round={rnd}"

    print("Scraping Round:", rnd)

    html = fetch(url)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")

    links = []

    for a in soup.find_all("a", href=True):
        href = a["href"]

        if "ft_match_statistics" not in href:
            continue

        if href.startswith("/"):
            href = BASE + href

        links.append(href)

    return sorted(set(links))


# -------------------------------
# PARSE MATCH
# -------------------------------
def parse_match(url, match_id):
    html = fetch(url)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")

    title = soup.find("title").text
    text = clean(title.replace("AFL Match Statistics :", ""))

    if " def " not in text:
        return []

    team_a, rest = text.split(" def ", 1)
    team_b = rest.split(" at ")[0]

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

        opponent = team_b if current_team == team_a else team_a

        data.append({
            "season": SEASON,
            "round": "Round 0",
            "venue": "",
            "match_id": match_id,

            "player": name,
            "played_for": current_team,
            "played_against": opponent,

            "K": to_int(cols[1].text),
            "HB": to_int(cols[2].text),
            "D": to_int(cols[3].text),
            "M": to_int(cols[4].text),
            "G": to_int(cols[5].text),
            "B": to_int(cols[6].text),
            "T": to_int(cols[7].text),
            "HO": to_int(cols[8].text),
            "FF": to_int(cols[14].text),
            "FA": to_int(cols[15].text),

            "home_team": team_a,
            "away_team": team_b,
            "home_points": 0,
            "away_points": 0,
            "margin": 0,
            "total_points": 0,

            "home_q1": 0,
            "home_q2": 0,
            "home_q3": 0,
            "home_q4": 0,
            "away_q1": 0,
            "away_q2": 0,
            "away_q3": 0,
            "away_q4": 0,

            "crowd": 0,
            "date": "",
            "date_iso": ""
        })

    return data


# -------------------------------
# MAIN
# -------------------------------
def main():
    links = get_links()

    all_rows = []
    match_id = 1

    for link in links:
        print("Match:", match_id)

        rows = parse_match(link, match_id)
        all_rows.extend(rows)

        match_id += 1
        time.sleep(5)  # 🔥 CRITICAL

    print("TOTAL ROWS:", len(all_rows))

    OUTPUT.write_text(json.dumps(all_rows, indent=2))
    print("✅ FIRST ROUND BUILT")


if __name__ == "__main__":
    main()
