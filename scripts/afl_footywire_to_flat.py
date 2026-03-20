import json
import re
import time
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

print("AFL FOOTYWIRE SCRAPER (HEADER LOCK FINAL)")

YEAR = 2026
BASE = "https://www.footywire.com/afl/footy/"
HEADERS = {"User-Agent": "Mozilla/5.0"}

OUT = Path(f"docs/data/afl/afl_{YEAR}.json")
PLAYERS_OUT = Path("docs/data/afl/players.json")
OUT.parent.mkdir(parents=True, exist_ok=True)


def clean(x):
    return re.sub(r"\s+", " ", (x or "")).strip()


def num(x):
    try:
        return int(clean(x).replace(",", ""))
    except:
        return 0


def slug(x):
    return re.sub(r"[^a-z0-9]+", "-", clean(x).lower()).strip("-")


def score_str(p):
    return f"{p//6}.{p%6} ({p})"


def html(url):
    return requests.get(url, headers=HEADERS, timeout=30).text


# -----------------------
# MATCH LINKS
# -----------------------
def get_links():
    soup = BeautifulSoup(html(f"{BASE}ft_match_list?year={YEAR}"), "html.parser")
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
    text = soup.get_text("\n")
    lines = [clean(x) for x in text.split("\n") if clean(x)]

    team_a = ""
    team_b = ""
    rnd = ""
    venue = ""
    crowd = ""
    date_iso = ""

    for i, line in enumerate(lines):
        if " defeats " in line:
            a, b = line.split(" defeats ")
            team_a, team_b = clean(a), clean(b)
            detail = lines[i+1]
            date_line = lines[i+2]
            break
        if " drew " in line:
            a, b = line.split(" drew ")
            team_a, team_b = clean(a), clean(b)
            detail = lines[i+1]
            date_line = lines[i+2]
            break

    r = re.search(r"(Round\s+\d+)", detail)
    if r:
        rnd = r.group(1)

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

    return team_a, team_b, rnd, venue, crowd, date_iso


# -----------------------
# SCOREBOARD
# -----------------------
def get_scores(soup):
    scores = {}

    for table in soup.find_all("table"):
        if "Final" not in table.get_text():
            continue

        for row in table.find_all("tr"):
            tds = row.find_all("td")
            if len(tds) < 2:
                continue

            team = clean(tds[0].text)
            score = num(tds[-1].text)

            if team and score:
                scores[team] = score

        if len(scores) >= 2:
            return scores

    return scores


# -----------------------
# 🔥 PLAYER TABLES (HEADER LOCK)
# -----------------------
def get_player_tables(soup):
    tables = []

    for table in soup.find_all("table"):

        headers = [clean(th.get_text()) for th in table.find_all("th")]

        if not headers:
            continue

        # THIS IS THE KEY CHECK
        if headers[:6] == ["Player", "K", "HB", "D", "M", "G"]:
            tables.append(table)

    return tables


# -----------------------
# PLAYER PARSER
# -----------------------
def parse_players(table):
    players = []

    for tr in table.find_all("tr")[1:]:
        tds = tr.find_all("td")

        if len(tds) < 18:
            continue

        link = tds[0].find("a")
        if not link:
            continue

        name = clean(link.text)

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

    return players


# -----------------------
# MATCH
# -----------------------
def parse_match(url, idx):
    soup = BeautifulSoup(html(url), "html.parser")

    team_a, team_b, rnd, venue, crowd, date_iso = parse_header(soup)
    scores = get_scores(soup)
    tables = get_player_tables(soup)

    print("TABLES:", len(tables))

    if len(tables) < 2:
        return []

    rows = []
    match_id = f"{YEAR}_{str(idx).zfill(4)}"

    for i in range(2):
        team = team_a if i == 0 else team_b
        opp = team_b if i == 0 else team_a

        players = parse_players(tables[i])

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
                "team_score": scores.get(team, 0),
                "opp_score": scores.get(opp, 0),
                "team_score_str": score_str(scores.get(team, 0)),
                "opp_score_str": score_str(scores.get(opp, 0)),
            })

    return rows


# -----------------------
# MAIN
# -----------------------
def main():
    links = get_links()
    all_rows = []

    for i, link in enumerate(links, 1):
        all_rows += parse_match(link, i)
        time.sleep(1)

    print("ROWS:", len(all_rows))

    if len(all_rows) == 0:
        print("FAILED")
        return

    json.dump(all_rows, open(OUT, "w"), indent=2)

    print("DONE")


if __name__ == "__main__":
    main()
