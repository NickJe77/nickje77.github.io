from pathlib import Path
import json
import csv
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs

print("AFL SCRAPER (WORKING - DIRECT SAVE)")

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
SEASON = 2026
FIXTURE_URL = f"https://www.footywire.com/afl/footy/ft_match_list?year={SEASON}"
BASE = "https://www.footywire.com"

DATA_DIR = Path("docs/data/afl")
DATA_DIR.mkdir(parents=True, exist_ok=True)

SEASON_JSON = DATA_DIR / f"afl_{SEASON}.json"
MATCHES_JSON = DATA_DIR / f"afl_{SEASON}_matches.json"
PLAYERS_JSON = DATA_DIR / f"players_{SEASON}.json"

HEADERS = {"User-Agent": "Mozilla/5.0"}

# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def clean(x):
    return re.sub(r"\s+", " ", (x or "")).strip()

def mid(url):
    return int(parse_qs(urlparse(url).query).get("mid", ["0"])[0])

def parse_qtr(q):
    if re.match(r"\d+\.\d+", q):
        return float(q)
    return 0.0

def get_soup(url):
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")

# -------------------------------------------------
# HEADER
# -------------------------------------------------
def extract_header(soup):
    text = soup.get_text("\n")
    lines = [clean(x) for x in text.split("\n") if clean(x)]

    round_name, venue, date, crowd = "", "", "", 0

    m = re.search(r"(Round\s+\d+),\s*(.*?),\s*Attendance:\s*([\d,]+)", text)
    if m:
        round_name = m.group(1)
        venue = m.group(2)
        crowd = int(m.group(3).replace(",", ""))

    for i, line in enumerate(lines):
        if "Round" in line and i+1 < len(lines):
            date = lines[i+1]
            break

    return round_name, venue, date, crowd

# -------------------------------------------------
# SCOREBOARD (LOCKED)
# -------------------------------------------------
def extract_scoreboard(soup):
    lines = [clean(x) for x in soup.get_text("\n").split("\n") if clean(x)]

    for i, line in enumerate(lines):
        if line == "Team Q1 Q2 Q3 Q4 Final":
            rows = []
            for l in lines[i+1:i+5]:
                m = re.match(r"^(.*?)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+)$", l)
                if m:
                    rows.append({
                        "team": clean(m.group(1)),
                        "q1": m.group(2),
                        "q2": m.group(3),
                        "q3": m.group(4),
                        "q4": m.group(5),
                        "final": int(m.group(6))
                    })
            if len(rows) == 2:
                return rows[0], rows[1]

    return None, None

# -------------------------------------------------
# PLAYER TABLE
# -------------------------------------------------
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

    round_name, venue, date, crowd = extract_header(soup)
    home, away = extract_scoreboard(soup)

    if not home:
        print("FAILED:", match_id)
        return []

    tables = []
    for h in soup.find_all(["b","font"]):
        if "Match Statistics" in h.text:
            team = clean(h.text.split("Match Statistics")[0])
            table = h.find_next("table")
            tables.append((team, table))

    home_rows = parse_table(tables[0][1], home["team"])
    away_rows = parse_table(tables[1][1], away["team"])

    margin = abs(home["final"] - away["final"])
    total = home["final"] + away["final"]

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
            "margin": margin,
            "total_points": total,
            "home_q1": parse_qtr(home["q1"]),
            "home_q2": parse_qtr(home["q2"]),
            "home_q3": parse_qtr(home["q3"]),
            "home_q4": parse_qtr(home["q4"]),
            "away_q1": parse_qtr(away["q1"]),
            "away_q2": parse_qtr(away["q2"]),
            "away_q3": parse_qtr(away["q3"]),
            "away_q4": parse_qtr(away["q4"]),
            "crowd": crowd,
            "date": date,
            "date_iso": ""
        })

    print("DONE:", match_id)
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
    all_rows.extend(scrape_match(u))
    time.sleep(0.3)

# -------------------------------------------------
# SAVE
# -------------------------------------------------
with open(SEASON_JSON, "w") as f:
    json.dump(all_rows, f, indent=2)

matches = {}
for r in all_rows:
    mid_ = r["match_id"]
    if mid_ not in matches:
        matches[mid_] = {
            "match_id": mid_,
            "round": r["round"],
            "home_team": r["home_team"],
            "away_team": r["away_team"],
            "home_score": r["home_points"],
            "away_score": r["away_points"]
        }

with open(MATCHES_JSON, "w") as f:
    json.dump(list(matches.values()), f, indent=2)

players = {}
for r in all_rows:
    players.setdefault(r["player"], {"player": r["player"], "games": []})["games"].append(r)

with open(PLAYERS_JSON, "w") as f:
    json.dump(list(players.values()), f, indent=2)

print("DONE ✅")
