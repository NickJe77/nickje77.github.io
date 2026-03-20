import json
import re
import time
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

print("AFL SCRAPER (FINAL FIXED)")

YEAR = 2026
BASE = "https://www.footywire.com/afl/footy/"
HEADERS = {"User-Agent": "Mozilla/5.0"}

OUT = Path(f"docs/data/afl/afl_{YEAR}.json")
OUT.parent.mkdir(parents=True, exist_ok=True)


def clean(x):
    return re.sub(r"\s+", " ", (x or "")).strip()


def num(x):
    try:
        return int(clean(x).replace(",", ""))
    except:
        return 0


def html(url):
    return requests.get(url, headers=HEADERS, timeout=30).text


# -----------------------
# LINKS
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
# SAFE HEADER PARSER
# -----------------------
def parse_header(soup):
    text = soup.get_text(" ")
    text = clean(text)

    # teams
    m = re.search(r"([A-Za-z ]+)\s+(defeats|drew)\s+([A-Za-z ]+)", text)

    if m:
        team_a = clean(m.group(1))
        team_b = clean(m.group(3))
    else:
        team_a = ""
        team_b = ""

    # round
    r = re.search(r"(Round\s+\d+)", text)
    rnd = r.group(1) if r else ""

    # venue
    v = re.search(r"Round\s+\d+,\s*([^,]+)", text)
    venue = clean(v.group(1)) if v else ""

    # crowd
    c = re.search(r"Attendance:\s*([\d,]+)", text)
    crowd = c.group(1).replace(",", "") if c else ""

    # date
    d = re.search(r"\w+,\s+\d+\s+\w+\s+\d{4},\s+\d+:\d+\s+\w+", text)
    date_iso = ""
    if d:
        try:
            safe = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", d.group(0))
            dt = datetime.strptime(safe, "%A, %d %B %Y, %I:%M %p AEDT")
            date_iso = dt.strftime("%Y-%m-%dT%H:%M:%S")
        except:
            pass

    return team_a, team_b, rnd, venue, crowd, date_iso


# -----------------------
# SCORE
# -----------------------
def get_scores(soup):
    scores = {}

    for row in soup.find_all("tr"):
        tds = row.find_all("td")
        if len(tds) < 2:
            continue

        team = clean(tds[0].text)
        val = num(tds[-1].text)

        if team and val:
            scores[team] = val

    return scores


# -----------------------
# 🔥 PLAYER TABLES (COLUMN BASED)
# -----------------------
def get_player_tables(soup):
    tables = []

    for table in soup.find_all("table"):
        rows = table.find_all("tr")

        if not rows:
            continue

        # check header row column count
        header = rows[0].find_all(["th", "td"])

        if len(header) >= 18:
            tables.append(table)

    return tables


# -----------------------
# PARSE PLAYERS
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
    tables = get_player_tables(soup)

    print("TABLES:", len(tables), "|", team_a, "vs", team_b)

    if len(tables) < 2:
        return []

    rows = []
    match_id = f"{YEAR}_{str(idx).zfill(4)}"

    for i in range(2):
        team = team_a if i == 0 else team_b
        opp = team_b if i == 0 else team_a

        for p in parse_players(tables[i]):
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
