import json
import re
import time
from pathlib import Path
from collections import defaultdict

import requests
from bs4 import BeautifulSoup

print("AFL PIPELINE (FOOTYWIRE STABLE)")

BASE = "https://www.footywire.com"
SEASON = 2026

DATA_DIR = Path("docs/data/afl")
OUTPUT = DATA_DIR / f"afl_{SEASON}.json"
PLAYERS_DIR = DATA_DIR / "players"
PLAYERS_JSON = DATA_DIR / "players.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)
PLAYERS_DIR.mkdir(parents=True, exist_ok=True)

# -------------------------------
# SESSION + HEADERS
# -------------------------------
session = requests.Session()

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-AU,en;q=0.9"
}

session.headers.update(HEADERS)


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
    for i in range(3):
        try:
            r = session.get(url, timeout=20)

            if r.status_code == 200 and "Match Statistics" in r.text:
                return r.text

        except Exception as e:
            print("Fetch error:", e)

        time.sleep(5)

    print("BLOCKED:", url)
    return None


# -------------------------------
# GET MATCH LINKS (LIMITED)
# -------------------------------
def get_links():
    links = []

    # 🔥 ONLY DO FIRST FEW ROUNDS (SAFE)
    for rnd in range(0, 5):
        url = f"{BASE}/afl/footy/ft_match_list?year={SEASON}&round={rnd}"

        print("Round:", rnd)

        html = fetch(url)
        if not html:
            continue

        soup = BeautifulSoup(html, "html.parser")

        for a in soup.find_all("a", href=True):
            href = a["href"]

            if "ft_match_statistics" not in href:
                continue

            if href.startswith("/"):
                href = BASE + href

            links.append(href)

        time.sleep(3)

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

    # -------------------------------
    # MATCH META
    # -------------------------------
    page_text = soup.get_text(" ")

    venue = ""
    m = re.search(r"Venue:\s*(.*?)\s", page_text)
    if m:
        venue = clean(m.group(1))

    crowd = 0
    m = re.search(r"Attendance:\s*(\d+)", page_text)
    if m:
        crowd = int(m.group(1))

    date = ""
    m = re.search(r"\w{3}\s\d{1,2}\s\w+\s\d{1,2}:\d{2}", page_text)
    if m:
        date = m.group(0)

    # -------------------------------
    # PLAYER TABLES
    # -------------------------------
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

        row = {
            "season": SEASON,
            "round": "",  # we can refine later
            "venue": venue,
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

            "crowd": crowd,
            "date": date,
            "date_iso": ""
        }

        data.append(row)

    return data


# -------------------------------
# BUILD PLAYERS
# -------------------------------
def build_players(rows):
    players = {}

    for r in rows:
        name = r["player"]

        if name not in players:
            players[name] = {
                "name": name,
                "games": [],
                "career": defaultdict(int),
            }

        players[name]["games"].append(r)

        for k, v in r.items():
            if isinstance(v, int):
                players[name]["career"][k] += v

    return players


def save_players(players):
    summary = []

    for name, p in players.items():
        slug = re.sub(r"[^a-z0-9\-]", "", name.lower().replace(" ", "-"))[:60]

        (PLAYERS_DIR / f"{slug}.json").write_text(json.dumps({
            "name": name,
            "career": dict(p["career"]),
            "games": p["games"]
        }, indent=2))

        summary.append({
            "name": name,
            "slug": slug,
            "games": len(p["games"])
        })

    PLAYERS_JSON.write_text(json.dumps(summary, indent=2))


# -------------------------------
# MAIN
# -------------------------------
def main():
    links = get_links()

    all_rows = []
    match_id = 0

    for link in links:
        match_id += 1
        print("Match:", match_id)

        time.sleep(4)

        rows = parse_match(link, match_id)
        all_rows.extend(rows)

    print("TOTAL ROWS:", len(all_rows))

    if len(all_rows) < 200:
        print("❌ BLOCKED — NOT SAVING")
        return

    OUTPUT.write_text(json.dumps(all_rows, indent=2))
    print("✅ DATA SAVED")

    players = build_players(all_rows)
    save_players(players)

    print("✅ PLAYERS BUILT")


if __name__ == "__main__":
    main()
