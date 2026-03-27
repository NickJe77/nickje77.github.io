from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from pathlib import Path
import csv
import json
import re
import time
from urllib.parse import urljoin, urlparse, parse_qs

print("AFL INCREMENTAL SCRAPER (FULL)")

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
SEASON = 2026
FIXTURE_URL = f"https://www.footywire.com/afl/footy/ft_match_list?year={SEASON}"

DESKTOP = Path.home() / "Desktop"

SEASON_JSON = DESKTOP / f"afl_{SEASON}.json"
MATCHES_JSON = DESKTOP / f"afl_{SEASON}_matches.json"
PLAYERS_JSON = DESKTOP / f"players_{SEASON}.json"

MATCHES_CSV = DESKTOP / f"afl_{SEASON}_matches.csv"
PLAYERS_CSV = DESKTOP / f"afl_{SEASON}_players.csv"

REBUILD_ALL = False   # 🔥 set True to rebuild everything

# -------------------------------------------------
# BROWSER
# -------------------------------------------------
def driver():
    o = Options()
    o.add_argument("--headless=new")
    o.add_argument("--window-size=1600,2000")
    return webdriver.Chrome(options=o)

# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def clean(x):
    return re.sub(r"\s+", " ", x).strip()

def is_number(x):
    try:
        float(x)
        return True
    except:
        return False

def mid(url):
    return parse_qs(urlparse(url).query).get("mid", [""])[0]

# -------------------------------------------------
# LOAD EXISTING DATA
# -------------------------------------------------
existing_rows = []
existing_ids = set()

if SEASON_JSON.exists() and not REBUILD_ALL:
    with open(SEASON_JSON) as f:
        existing_rows = json.load(f)
        existing_ids = {r["match_id"] for r in existing_rows}

print("Existing matches:", len(existing_ids))

# -------------------------------------------------
# GET MATCH URLS
# -------------------------------------------------
def get_urls(d):
    print("Loading fixture page...")
    d.get(FIXTURE_URL)
    time.sleep(8)

    soup = BeautifulSoup(d.page_source, "html.parser")

    urls = []
    for a in soup.find_all("a", href=True):
        if "ft_match_statistics?mid=" in a["href"]:
            urls.append(urljoin(FIXTURE_URL, a["href"]))

    urls = list(set(urls))
    print("Found matches:", len(urls))
    return urls

# -------------------------------------------------
# SCOREBOARD
# -------------------------------------------------
def scoreboard(lines):
    for i in range(len(lines)):
        if re.match(r"^[A-Za-z ]+$", lines[i]):
            if i + 11 < len(lines):
                if lines[i+5].isdigit():
                    return [
                        {
                            "team": lines[i],
                            "q1": lines[i+1],
                            "q2": lines[i+2],
                            "q3": lines[i+3],
                            "q4": lines[i+4],
                            "final": int(lines[i+5])
                        },
                        {
                            "team": lines[i+6],
                            "q1": lines[i+7],
                            "q2": lines[i+8],
                            "q3": lines[i+9],
                            "q4": lines[i+10],
                            "final": int(lines[i+11])
                        }
                    ]
    return None

# -------------------------------------------------
# SCRAPE MATCH
# -------------------------------------------------
def scrape(d, url):

    match_id = mid(url)

    if match_id in existing_ids:
        return None

    d.get(url)
    time.sleep(3)

    soup = BeautifulSoup(d.page_source, "html.parser")

    text = soup.get_text("\n")
    lines = [clean(x) for x in text.split("\n") if clean(x)]

    sb = scoreboard(lines)
    if not sb:
        print("FAILED:", match_id)
        return None

    home, away = sb

    tables = []
    for h in soup.find_all(["b","font"]):
        t = clean(h.get_text())
        if "Match Statistics" in t:
            team = re.sub(r"\s*\(.*?\)", "", t.split("Match Statistics")[0]).strip()
            table = h.find_next("table")
            tables.append((team, table))

    if len(tables) < 2:
        print("NO TABLES:", match_id)
        return None

    def parse(tbl, team):
        out = []
        seen = set()

        for r in tbl.find_all("tr"):
            cols = [clean(td.text) for td in r.find_all("td")]

            if not cols:
                continue
            if cols[0].lower() == "player":
                continue
            if not any(is_number(c) for c in cols[1:]):
                continue

            name = cols[0]
            if name in seen:
                continue
            seen.add(name)

            stats = [int(float(c)) if is_number(c) else 0 for c in cols[1:]]
            while len(stats) < 10:
                stats.append(0)

            out.append((name, team, stats))

        return out

    home_rows = parse(tables[0][1], home["team"])
    away_rows = parse(tables[1][1], away["team"])

    rows = []

    for name, team, s in home_rows + away_rows:
        rows.append({
            "season": SEASON,
            "match_id": match_id,
            "player": name,
            "played_for": team,
            "played_against": away["team"] if team == home["team"] else home["team"],
            "home_team": home["team"],
            "away_team": away["team"],
            "home_points": home["final"],
            "away_points": away["final"],
            "K": s[0],"HB": s[1],"D": s[2],
            "M": s[3],"G": s[4],"B": s[5],
            "T": s[6],"HO": s[7],
            "FF": s[8],"FA": s[9],
            "footywire_url": url
        })

    print("NEW:", match_id, home["team"], "vs", away["team"])
    return rows

# -------------------------------------------------
# RUN
# -------------------------------------------------
d = driver()

urls = get_urls(d)

new_rows = []

for u in urls:
    r = scrape(d, u)
    if r:
        new_rows.extend(r)

d.quit()

print("New rows:", len(new_rows))

# -------------------------------------------------
# MERGE
# -------------------------------------------------
all_rows = existing_rows + new_rows

# -------------------------------------------------
# SAVE MAIN JSON
# -------------------------------------------------
with open(SEASON_JSON, "w") as f:
    json.dump(all_rows, f, indent=2)

print("UPDATED:", SEASON_JSON)

# -------------------------------------------------
# BUILD MATCHES
# -------------------------------------------------
matches = {}

for r in all_rows:
    mid = r["match_id"]
    if mid not in matches:
        matches[mid] = {
            "match_id": mid,
            "home_team": r["home_team"],
            "away_team": r["away_team"],
            "home_score": r["home_points"],
            "away_score": r["away_points"]
        }

# SAVE MATCHES JSON
with open(MATCHES_JSON, "w") as f:
    json.dump(list(matches.values()), f, indent=2)

print("UPDATED:", MATCHES_JSON)

# SAVE MATCHES CSV
if matches:
    with open(MATCHES_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(matches.values())[0].keys())
        writer.writeheader()
        writer.writerows(matches.values())

# -------------------------------------------------
# BUILD PLAYERS
# -------------------------------------------------
players = {}

for r in all_rows:
    name = r["player"]

    if name not in players:
        players[name] = {
            "player": name,
            "games": []
        }

    players[name]["games"].append(r)

# SAVE PLAYERS JSON
with open(PLAYERS_JSON, "w") as f:
    json.dump(list(players.values()), f, indent=2)

print("UPDATED:", PLAYERS_JSON)

# SAVE PLAYERS CSV
if all_rows:
    with open(PLAYERS_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=all_rows[0].keys())
        writer.writeheader()
        writer.writerows(all_rows)

print("DONE ✅")
