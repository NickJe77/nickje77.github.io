import json
import re
import time
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

print("AFL FOOTYWIRE SCRAPER (HARD LOCK VERSION)")

YEAR = 2026
BASE = "https://www.footywire.com/afl/footy/"
HEADERS = {"User-Agent": "Mozilla/5.0"}

SEASON_OUTPUT = Path(f"docs/data/afl/afl_{YEAR}.json")
PLAYERS_OUTPUT = Path("docs/data/afl/players.json")
SEASON_OUTPUT.parent.mkdir(parents=True, exist_ok=True)


# -----------------------
# HELPERS
# -----------------------
def clean(x):
    return re.sub(r"\s+", " ", (x or "")).strip()

def num(x):
    try:
        return int(clean(x).replace(",", ""))
    except:
        return 0

def slug(x):
    return re.sub(r"[^a-z0-9]+", "-", clean(x).lower()).strip("-")

def format_score(p):
    return f"{p//6}.{p%6} ({p})"

def get_html(url):
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text


# -----------------------
# MATCH LINKS
# -----------------------
def get_links():
    soup = BeautifulSoup(get_html(f"{BASE}ft_match_list?year={YEAR}"), "html.parser")
    links = []

    for a in soup.select("a[href*='ft_match_statistics?mid=']"):
        href = a["href"]
        full = href if href.startswith("http") else BASE + href
        if full not in links:
            links.append(full)

    print("MATCHES:", len(links))
    return links


# -----------------------
# HEADER
# -----------------------
def parse_header(soup):
    txt = soup.get_text("\n")
    lines = [clean(x) for x in txt.split("\n") if clean(x)]

    team_a = ""
    team_b = ""
    round_name = ""
    venue = ""
    crowd = ""
    date_iso = ""

    for i, line in enumerate(lines):
        if " defeats " in line:
            a, b = line.split(" defeats ", 1)
            team_a, team_b = clean(a), clean(b)
            detail = lines[i+1] if i+1 < len(lines) else ""
            date_line = lines[i+2] if i+2 < len(lines) else ""
            break

        if " drew " in line:
            a, b = line.split(" drew ", 1)
            team_a, team_b = clean(a), clean(b)
            detail = lines[i+1] if i+1 < len(lines) else ""
            date_line = lines[i+2] if i+2 < len(lines) else ""
            break

    r = re.search(r"(Round\s+\d+)", detail)
    if r:
        round_name = r.group(1)

    parts = [clean(x) for x in detail.split(",")]
    if len(parts) >= 2:
        venue = parts[1]

    c = re.search(r"Attendance:\s*([\d,]+)", detail)
    if c:
        crowd = c.group(1).replace(",", "")

    safe = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", date_line)

    for fmt in [
        "%A, %d %B %Y, %I:%M %p AEDT",
        "%A, %d %B %Y, %I:%M %p AEST"
    ]:
        try:
            dt = datetime.strptime(safe, fmt)
            date_iso = dt.strftime("%Y-%m-%dT%H:%M:%S")
            break
        except:
            pass

    return team_a, team_b, round_name, venue, crowd, date_iso


# -----------------------
# SCOREBOARD
# -----------------------
def extract_scoreboard(soup):
    scores = {}

    for table in soup.find_all("table"):
        if "Final" not in table.get_text():
            continue

        rows = table.find_all("tr")
        for row in rows:
            tds = row.find_all("td")
            if len(tds) < 2:
                continue

            team = clean(tds[0].get_text())
            score = num(tds[-1].get_text())

            if team and score:
                scores[team] = score

        if len(scores) >= 2:
            return scores

    return scores


# -----------------------
# PLAYER TABLES (STRICT)
# -----------------------
def get_player_tables(soup):
    tables = []

    for table in soup.find_all("table"):
        rows = table.find_all("tr")

        if len(rows) < 15:
            continue

        # must contain player links
        links = table.select("a[href*='player']")
        if len(links) < 15:
            continue

        tables.append(table)

    return tables


# -----------------------
# PLAYER PARSER (LOCKED)
# -----------------------
def parse_players(table):
    players = []

    for tr in table.find_all("tr"):
        tds = tr.find_all("td")

        if len(tds) < 18:
            continue

        a = tds[0].find("a")
        if not a:
            continue

        name = clean(a.get_text())
        if len(name.split()) < 2:
            continue

        try:
            players.append({
                "player": name,
                "K": num(tds[1].text),
                "HB": num(tds[2].text),
                "D": num(tds[3].text),
                "M": num(tds[4].text),
                "G": num(tds[5].text),
                "B": num(tds[6].text),
                "T": num(tds[7].text),
                "HO": num(tds[8].text),
                "GA": num(tds[9].text),
                "I50": num(tds[10].text),
                "CL": num(tds[11].text),
                "CG": num(tds[12].text),
                "R50": num(tds[13].text),
                "FF": num(tds[14].text),
                "FA": num(tds[15].text),
                "AF": num(tds[16].text),
                "SC": num(tds[17].text),
            })
        except:
            continue

    return players


# -----------------------
# MATCH PARSER
# -----------------------
def parse_match(url, idx):
    soup = BeautifulSoup(get_html(url), "html.parser")

    team_a, team_b, rnd, venue, crowd, date_iso = parse_header(soup)
    scores = extract_scoreboard(soup)
    tables = get_player_tables(soup)

    print("TABLES:", len(tables))

    if len(tables) < 2:
        return []

    match_id = f"{YEAR}_{str(idx).zfill(4)}"

    rows = []

    for i in range(2):
        team = team_a if i == 0 else team_b
        opp = team_b if i == 0 else team_a

        players = parse_players(tables[i])

        if not players:
            return []

        team_score = scores.get(team, 0)
        opp_score = scores.get(opp, 0)

        for p in players:
            rows.append({
                "match_id": match_id,
                "season": YEAR,
                "round": rnd,
                "player": p["player"],
                "played_for": team,
                "played_against": opp,
                **p,
                "date_iso": date_iso,
                "venue": venue,
                "crowd": crowd,
                "team_score": team_score,
                "opp_score": opp_score,
                "team_score_str": format_score(team_score),
                "opp_score_str": format_score(opp_score),
            })

    return rows


# -----------------------
# PLAYERS.JSON
# -----------------------
def build_players(rows):
    players = {}

    for r in rows:
        name = r["player"]

        if name not in players:
            players[name] = {
                "player": name,
                "slug": slug(name),
                "games": 0,
                "teams": set()
            }

        players[name]["games"] += 1
        players[name]["teams"].add(r["played_for"])

    out = []
    for p in players.values():
        p["teams"] = sorted(p["teams"])
        p["team"] = p["teams"][-1] if p["teams"] else ""
        out.append(p)

    return sorted(out, key=lambda x: x["player"])


# -----------------------
# MAIN
# -----------------------
def main():
    links = get_links()
    all_rows = []

    for i, link in enumerate(links, 1):
        try:
            rows = parse_match(link, i)
            all_rows.extend(rows)
        except Exception as e:
            print("ERROR:", link, e)

        time.sleep(1)

    print("TOTAL ROWS:", len(all_rows))

    if len(all_rows) < 100:
        print("FAILED - NOT SAVING")
        return

    with open(SEASON_OUTPUT, "w") as f:
        json.dump(all_rows, f, indent=2)

    with open(PLAYERS_OUTPUT, "w") as f:
        json.dump(build_players(all_rows), f, indent=2)

    print("DONE")


if __name__ == "__main__":
    main()
