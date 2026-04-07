import requests
from bs4 import BeautifulSoup
from pathlib import Path
import json
import re
import time
from urllib.parse import urljoin, urlparse, parse_qs

print("AFL SCRAPER (ROBUST VERSION)")

SEASON = 2026
BASE = "https://www.footywire.com"
FIXTURE_URL = f"{BASE}/afl/footy/ft_match_list?year={SEASON}"

DATA_DIR = Path("docs/data/afl")
DATA_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def clean(x):
    return re.sub(r"\s+", " ", (x or "")).strip()

def mid(url):
    return int(parse_qs(urlparse(url).query).get("mid", ["0"])[0])

def get_soup(url):
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")

# -------------------------------------------------
# SCOREBOARD (ROBUST DETECTION)
# -------------------------------------------------
def extract_scoreboard(soup):

    tables = soup.find_all("table")

    for table in tables:
        rows = table.find_all("tr")

        parsed = []

        for r in rows:
            cols = [clean(td.text) for td in r.find_all("td")]

            # Must look like:
            # Team | 3.2 | 5.6 | 7.8 | 10.10 | 70
            if len(cols) != 6:
                continue

            # team must not contain numbers
            if any(c.isdigit() for c in cols[0]):
                continue

            # quarter format must be X.X
            if not re.match(r"^\d+\.\d+$", cols[1]):
                continue

            # final must be integer
            if not cols[5].isdigit():
                continue

            parsed.append({
                "team": cols[0],
                "q1": cols[1],
                "q2": cols[2],
                "q3": cols[3],
                "q4": cols[4],
                "final": int(cols[5])
            })

        if len(parsed) == 2:
            return parsed[0], parsed[1]

    return None, None

# -------------------------------------------------
# HEADER
# -------------------------------------------------
def extract_header(soup):
    text = soup.get_text("\n")

    round_name = ""
    venue = ""
    crowd = 0
    date = ""

    m = re.search(r"(Round\s+\d+),\s*(.*?),\s*Attendance:\s*([\d,]+)", text)
    if m:
        round_name = m.group(1)
        venue = m.group(2)
        crowd = int(m.group(3).replace(",", ""))

    lines = [clean(x) for x in text.split("\n") if clean(x)]

    for i, l in enumerate(lines):
        if "Round" in l and i+1 < len(lines):
            date = lines[i+1]
            break

    return round_name, venue, date, crowd

# -------------------------------------------------
# PLAYER TABLE
# -------------------------------------------------
def extract_player_tables(soup):

    tables = soup.find_all("table")
    results = []

    for table in tables:
        text = table.get_text()

        if "Player" in text and "K" in text and "HB" in text:
            prev = table.find_previous(["b", "font"])

            if prev and "Match Statistics" in prev.text:
                team = clean(prev.text.split("Match Statistics")[0])
                results.append((team, table))

    return results[:2]

def parse_table(tbl, team):

    rows = []
    seen = set()

    for tr in tbl.find_all("tr"):
        cols = [clean(td.text) for td in tr.find_all("td")]

        if len(cols) < 5 or cols[0] == "Player":
            continue

        name = cols[0]

        if name in seen:
            continue
        seen.add(name)

        stats = [int(float(c)) if c.replace('.','',1).isdigit() else 0 for c in cols[1:]]

        while len(stats) < 10:
            stats.append(0)

        rows.append((name, team, stats))

    return rows

# -------------------------------------------------
# SCRAPE MATCH
# -------------------------------------------------
def scrape_match(url):

    match_id = mid(url)
    soup = get_soup(url)

    home, away = extract_scoreboard(soup)

    if not home:
        print("SKIPPED (no valid scoreboard):", match_id)
        return []

    round_name, venue, date, crowd = extract_header(soup)

    tables = extract_player_tables(soup)

    if len(tables) < 2:
        print("SKIPPED (no player tables):", match_id)
        return []

    home_rows = parse_table(tables[0][1], home["team"])
    away_rows = parse_table(tables[1][1], away["team"])

    rows = []

    for name, team, s in home_rows + away_rows:
        rows.append({
            "season": SEASON,
            "round": round_name,
            "venue": venue,
            "match_id": match_id,
            "player": name,
            "played_for": team,
            "played_against": away["team"] if team == home["team"] else home["team"],
            "K": s[0], "HB": s[1], "D": s[2],
            "M": s[3], "G": s[4], "B": s[5],
            "T": s[6], "HO": s[7],
            "FF": s[8], "FA": s[9],
            "home_team": home["team"],
            "away_team": away["team"],
            "home_points": home["final"],
            "away_points": away["final"],
            "margin": abs(home["final"] - away["final"]),
            "total_points": home["final"] + away["final"],
            "crowd": crowd,
            "date": date,
            "date_iso": ""
        })

    print("OK:", match_id, home["final"], "-", away["final"])
    return rows

# -------------------------------------------------
# RUN
# -------------------------------------------------
fixture = get_soup(FIXTURE_URL)

urls = list(set(
    urljoin(BASE, a["href"])
    for a in fixture.find_all("a", href=True)
    if "ft_match_statistics?mid=" in a["href"]
))

all_rows = []

for u in urls:
    try:
        all_rows.extend(scrape_match(u))
        time.sleep(0.3)
    except Exception as e:
        print("ERROR:", u)

# -------------------------------------------------
# SAVE
# -------------------------------------------------
with open(DATA_DIR / f"afl_{SEASON}.json", "w") as f:
    json.dump(all_rows, f, indent=2)

print("DONE ✅")
