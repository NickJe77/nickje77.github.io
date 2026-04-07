import requests
from bs4 import BeautifulSoup
from pathlib import Path
import json
import csv
import re
import time
from urllib.parse import urljoin, urlparse, parse_qs

print("AFL SCRAPER (WORKING VERSION - MATCH STATS AS SOURCE OF TRUTH)")

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
SEASON = 2026
FIXTURE_URL = f"https://www.footywire.com/afl/footy/ft_match_list?year={SEASON}"
BASE = "https://www.footywire.com"

DESKTOP = Path.home() / "Desktop"

SEASON_JSON = DESKTOP / f"afl_{SEASON}.json"
MATCHES_JSON = DESKTOP / f"afl_{SEASON}_matches.json"
PLAYERS_JSON = DESKTOP / f"players_{SEASON}.json"

MATCHES_CSV = DESKTOP / f"afl_{SEASON}_matches.csv"
PLAYERS_CSV = DESKTOP / f"afl_{SEASON}_players.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    )
}

# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def clean(x):
    return re.sub(r"\s+", " ", (x or "")).strip()

def mid(url):
    return int(parse_qs(urlparse(url).query).get("mid", ["0"])[0])

def parse_qtr(q):
    q = clean(q)
    if re.fullmatch(r"\d+\.\d+", q):
        return float(q)
    return 0.0

def get_soup(url, retries=3, sleep=2):
    last_err = None
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            r.raise_for_status()
            return BeautifulSoup(r.text, "html.parser")
        except Exception as e:
            last_err = e
            if attempt < retries - 1:
                time.sleep(sleep)
    raise last_err

def get_text_lines(soup):
    text = soup.get_text("\n")
    return [clean(x) for x in text.split("\n") if clean(x)]

def parse_date_iso(date_text):
    # Leave blank to preserve your current structure
    return ""

def team_name_ok(x):
    x = clean(x)
    if not x:
        return False
    if re.search(r"\d", x):
        return False
    bad = {
        "Team", "Final", "Player", "Statistic", "Attribute",
        "Score", "Games", "Coach", "Result", "Attendance"
    }
    return x not in bad

# -------------------------------------------------
# HEADER
# -------------------------------------------------
def extract_header(soup):
    lines = get_text_lines(soup)
    text = "\n".join(lines)

    round_name = ""
    venue = ""
    date = ""
    crowd = 0

    # Example on stats page:
    # Round 4, MCG, Attendance: 84712
    # Monday, 6th April 2026, 3:15 PM AEST
    m = re.search(r"(Round\s+\d+|Elimination Final|Qualifying Final|Semi Final|Preliminary Final|Grand Final),\s*(.*?),\s*Attendance:\s*([\d,]+)", text)
    if m:
        round_name = clean(m.group(1))
        venue = clean(m.group(2))
        crowd = int(m.group(3).replace(",", ""))

    # Date line is normally next line after the round/venue line
    for i, line in enumerate(lines):
        if re.search(r"(Round\s+\d+|Elimination Final|Qualifying Final|Semi Final|Preliminary Final|Grand Final),", line):
            if i + 1 < len(lines):
                date = lines[i + 1]
            break

    return round_name, venue, date, crowd

# -------------------------------------------------
# SCOREBOARD
# -------------------------------------------------
def extract_scoreboard(soup):
    lines = get_text_lines(soup)

    # We anchor off the explicit scoreboard header found on match pages:
    # Team Q1 Q2 Q3 Q4 Final
    # Hawthorn 3.3 7.5 10.9 13.14 92
    # Geelong 2.1 9.2 10.5 14.7 91
    #
    # This exact structure appears on the stats page for mid=11440. :contentReference[oaicite:1]{index=1}
    start_idx = -1
    for i, line in enumerate(lines):
        if clean(line) == "Team Q1 Q2 Q3 Q4 Final":
            start_idx = i
            break

    if start_idx == -1:
        return None, None

    parsed = []

    for line in lines[start_idx + 1:start_idx + 10]:
        m = re.match(r"^(.*?)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+)$", line)
        if not m:
            continue

        team = clean(m.group(1))
        if not team_name_ok(team):
            continue

        parsed.append({
            "team": team,
            "q1": m.group(2),
            "q2": m.group(3),
            "q3": m.group(4),
            "q4": m.group(5),
            "final": int(m.group(6)),
        })

        if len(parsed) == 2:
            return parsed[0], parsed[1]

    return None, None

# -------------------------------------------------
# PLAYER TABLES
# -------------------------------------------------
def extract_player_tables(soup):
    lines = get_text_lines(soup)

    # Example:
    # Hawthorn Match Statistics (Sorted by Disposals) Coach: Sam Mitchell
    # ...
    # Geelong Match Statistics (Sorted by Disposals) Coach: Chris Scott
    #
    # This wording appears on the match page for mid=11440. :contentReference[oaicite:2]{index=2}
    team_headers = []
    for line in lines:
        m = re.match(r"^(.*?)\s+Match Statistics\s+\(Sorted by Disposals\)", line)
        if m:
            team = clean(m.group(1))
            if team_name_ok(team):
                team_headers.append(team)

    # Fall back to scanning tables for a player header row
    tables = soup.find_all("table")
    found = []

    for table in tables:
        table_text = clean(table.get_text(" ", strip=True))
        if "Player" not in table_text:
            continue
        if " K " not in f" {table_text} " and " HB " not in f" {table_text} ":
            continue

        # Find the nearest previous bold/font text that names the team
        team = None
        prev = table.find_previous(["b", "font"])
        hops = 0
        while prev and hops < 8:
            txt = clean(prev.get_text(" ", strip=True))
            m = re.match(r"^(.*?)\s+Match Statistics", txt)
            if m:
                possible_team = clean(m.group(1))
                if team_name_ok(possible_team):
                    team = possible_team
                    break
            prev = prev.find_previous(["b", "font"])
            hops += 1

        if team:
            found.append((team, table))

    # Deduplicate by team and keep first two
    out = []
    seen = set()
    for team, table in found:
        if team not in seen:
            seen.add(team)
            out.append((team, table))
        if len(out) == 2:
            break

    # If team headers exist but table assignment failed, keep best effort ordering
    return out

def parse_player_table(tbl, team):
    out = []
    seen = set()

    for r in tbl.find_all("tr"):
        cols = [clean(td.get_text(" ", strip=True)) for td in r.find_all("td")]
        if not cols:
            continue

        # Header row
        if cols[0] == "Player":
            continue

        # Must start with player name and have enough numeric cells
        name = cols[0]
        if not name or not team_name_ok(name.replace("'", "")) and len(cols) < 6:
            continue

        # We only need the first 10 stat columns after player:
        # K HB D M G B T HO FF FA
        nums = []
        for c in cols[1:]:
            if re.fullmatch(r"-?\d+(?:\.\d+)?", c):
                nums.append(int(float(c)))

        if len(nums) < 10:
            continue

        if name in seen:
            continue
        seen.add(name)

        stats = nums[:10]
        out.append((name, team, stats))

    return out

# -------------------------------------------------
# SCRAPE MATCH
# -------------------------------------------------
def scrape_match(url):
    match_id = mid(url)
    soup = get_soup(url)

    round_name, venue, date, crowd = extract_header(soup)
    home, away = extract_scoreboard(soup)

    if not home or not away:
        print("FAILED SCOREBOARD:", match_id, url)
        return []

    player_tables = extract_player_tables(soup)
    if len(player_tables) < 2:
        print("FAILED PLAYER TABLES:", match_id, url)
        return []

    # Match player tables to scoreboard teams
    table_map = {team: tbl for team, tbl in player_tables}

    # Best effort team normalization
    def get_tbl_for(team_name):
        if team_name in table_map:
            return table_map[team_name]
        for k, v in table_map.items():
            if clean(k).lower() == clean(team_name).lower():
                return v
        return None

    home_tbl = get_tbl_for(home["team"])
    away_tbl = get_tbl_for(away["team"])

    if home_tbl is None or away_tbl is None:
        print("FAILED TEAM MAP:", match_id, "| scoreboard:", home["team"], away["team"], "| tables:", list(table_map.keys()))
        return []

    home_rows = parse_player_table(home_tbl, home["team"])
    away_rows = parse_player_table(away_tbl, away["team"])

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
            "K": s[0],
            "HB": s[1],
            "D": s[2],
            "M": s[3],
            "G": s[4],
            "B": s[5],
            "T": s[6],
            "HO": s[7],
            "FF": s[8],
            "FA": s[9],
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
            "date_iso": parse_date_iso(date),
        })

    print("DONE:", match_id, "|", round_name, "|", home["team"], home["final"], "-", away["team"], away["final"])
    return rows

# -------------------------------------------------
# GET MATCH URLS
# -------------------------------------------------
def get_match_urls():
    soup = get_soup(FIXTURE_URL)

    # Match list page contains links to ft_match_statistics?mid=...
    # The 2026 fixture page is available at this URL. :contentReference[oaicite:3]{index=3}
    urls = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "ft_match_statistics?mid=" not in href:
            continue

        full = urljoin(BASE, href)
        if full not in seen:
            seen.add(full)
            urls.append(full)

    # Sort by match id for stable output
    urls.sort(key=mid)
    return urls

# -------------------------------------------------
# RUN
# -------------------------------------------------
all_rows = []
urls = get_match_urls()
print("FOUND MATCHES:", len(urls))

for url in urls:
    try:
        all_rows.extend(scrape_match(url))
        time.sleep(0.5)
    except Exception as e:
        print("ERROR:", url, "|", e)

# -------------------------------------------------
# SAVE MAIN JSON
# -------------------------------------------------
with open(SEASON_JSON, "w", encoding="utf-8") as f:
    json.dump(all_rows, f, indent=2, ensure_ascii=False)

print("UPDATED:", SEASON_JSON)

# -------------------------------------------------
# MATCHES JSON
# -------------------------------------------------
matches = {}

for r in all_rows:
    match_id = r["match_id"]
    if match_id not in matches:
        matches[match_id] = {
            "match_id": match_id,
            "round": r["round"],
            "home_team": r["home_team"],
            "away_team": r["away_team"],
            "home_score": r["home_points"],
            "away_score": r["away_points"],
            "venue": r["venue"],
            "crowd": r["crowd"],
            "date": r["date"],
            "date_iso": r["date_iso"],
        }

with open(MATCHES_JSON, "w", encoding="utf-8") as f:
    json.dump(list(matches.values()), f, indent=2, ensure_ascii=False)

print("UPDATED:", MATCHES_JSON)

# -------------------------------------------------
# PLAYERS JSON
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

with open(PLAYERS_JSON, "w", encoding="utf-8") as f:
    json.dump(list(players.values()), f, indent=2, ensure_ascii=False)

print("UPDATED:", PLAYERS_JSON)

# -------------------------------------------------
# CSV OUTPUTS
# -------------------------------------------------
if matches:
    with open(MATCHES_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(matches.values())[0].keys())
        writer.writeheader()
        writer.writerows(matches.values())

if all_rows:
    with open(PLAYERS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_rows[0].keys())
        writer.writeheader()
        writer.writerows(all_rows)

print("DONE ✅")
