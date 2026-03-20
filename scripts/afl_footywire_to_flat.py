import json
import re
import time
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

print("AFL FOOTYWIRE SCRAPER (LOCKED FIX VERSION)")

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
    x = clean(x).replace(",", "")
    try:
        return int(x)
    except:
        return 0


def slug(x):
    x = clean(x).lower()
    x = re.sub(r"[^a-z0-9]+", "-", x)
    return x.strip("-")


def format_score(points):
    return f"{points//6}.{points%6} ({points})"


def get_html(url):
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text


# -----------------------
# TEAM CLEAN
# -----------------------
def extract_team_name(title):
    title = clean(title)
    title = title.replace("AFL Match Statistics :", "")
    title = title.replace("Match Statistics", "")
    title = title.replace("Player Statistics", "")
    title = title.replace("Player Stats", "")
    return clean(title)


# -----------------------
# MATCH LINKS
# -----------------------
def get_links():
    url = f"{BASE}ft_match_list?year={YEAR}"
    soup = BeautifulSoup(get_html(url), "html.parser")

    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "ft_match_statistics?mid=" in href:
            full = href if href.startswith("http") else BASE + href
            if full not in links:
                links.append(full)

    print("MATCHES:", len(links))
    return links


# -----------------------
# HEADER
# -----------------------
def parse_header(soup):
    lines = [clean(x) for x in soup.get_text("\n").split("\n") if clean(x)]

    result = ""
    detail = ""
    date_line = ""

    for i, line in enumerate(lines):
        if " defeats " in line or " drew " in line:
            result = line
            detail = lines[i+1] if i+1 < len(lines) else ""
            date_line = lines[i+2] if i+2 < len(lines) else ""
            break

    team_a = ""
    team_b = ""

    if " defeats " in result:
        a, b = result.split(" defeats ", 1)
        team_a, team_b = clean(a), clean(b)
    elif " drew " in result:
        a, b = result.split(" drew ", 1)
        team_a, team_b = clean(a), clean(b)

    round_name = ""
    venue = ""
    crowd = ""

    r = re.search(r"(Round\s+\d+|Final.*)", detail, re.I)
    if r:
        round_name = clean(r.group(1))

    parts = [clean(x) for x in detail.split(",")]
    if len(parts) >= 2:
        venue = parts[1]

    c = re.search(r"Attendance:\s*([\d,]+)", detail)
    if c:
        crowd = c.group(1).replace(",", "")

    date_iso = ""
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

    return {
        "team_a": team_a,
        "team_b": team_b,
        "round": round_name,
        "venue": venue,
        "crowd": crowd,
        "date_iso": date_iso
    }


# -----------------------
# SCOREBOARD
# -----------------------
def extract_scoreboard(soup):
    scores = {}

    for table in soup.find_all("table"):
        txt = table.get_text(" ")

        if not all(x in txt for x in ["Q1", "Q2", "Q3", "Q4", "Final"]):
            continue

        rows = table.find_all("tr")

        for row in rows[1:3]:
            tds = row.find_all("td")
            if len(tds) < 2:
                continue

            team = clean(tds[0].get_text())
            score = num(tds[-1].get_text())

            if team:
                scores[team] = score

        if len(scores) == 2:
            return scores

    return scores


# -----------------------
# 🔥 PLAYER TABLE FIX (CRITICAL)
# -----------------------
def get_player_tables(soup):
    tables = []

    for table in soup.find_all("table"):

        text = table.get_text(" ")

        # HARD FILTER
        if "Player" not in text:
            continue
        if "Disposals" not in text:
            continue
        if "K" not in text or "HB" not in text:
            continue

        rows = table.find_all("tr")

        valid_rows = 0
        for r in rows:
            tds = r.find_all("td")
            if len(tds) >= 18 and tds[1].get_text().strip().isdigit():
                valid_rows += 1

        if valid_rows < 10:
            continue

        # find team name above
        team = ""
        prev = table.find_previous(["h1", "h2", "h3", "div", "td"])

        for _ in range(10):
            if not prev:
                break
            txt = clean(prev.get_text())
            if "Match Statistics" in txt:
                team = txt
                break
            prev = prev.find_previous(["h1", "h2", "h3", "div", "td"])

        team = extract_team_name(team)

        tables.append({
            "team": team,
            "table": table
        })

    return tables


# -----------------------
# PLAYER PARSER
# -----------------------
def parse_players(table):
    out = []

    for tr in table.find_all("tr"):
        tds = tr.find_all("td")

        if len(tds) < 18:
            continue

        name = clean(tds[0].get_text())

        if not name or len(name.split()) < 2:
            continue

        if not tds[1].get_text().strip().isdigit():
            continue

        out.append({
            "player": name,
            "K": num(tds[1].get_text()),
            "HB": num(tds[2].get_text()),
            "D": num(tds[3].get_text()),
            "M": num(tds[4].get_text()),
            "G": num(tds[5].get_text()),
            "B": num(tds[6].get_text()),
            "T": num(tds[7].get_text()),
            "HO": num(tds[8].get_text()),
            "GA": num(tds[9].get_text()),
            "I50": num(tds[10].get_text()),
            "CL": num(tds[11].get_text()),
            "CG": num(tds[12].get_text()),
            "R50": num(tds[13].get_text()),
            "FF": num(tds[14].get_text()),
            "FA": num(tds[15].get_text()),
            "AF": num(tds[16].get_text()),
            "SC": num(tds[17].get_text()),
        })

    return out


# -----------------------
# MATCH PARSER
# -----------------------
def parse_match(url, idx):
    soup = BeautifulSoup(get_html(url), "html.parser")

    match_id = f"{YEAR}_{str(idx).zfill(4)}"

    header = parse_header(soup)
    scores = extract_scoreboard(soup)
    tables = get_player_tables(soup)

    print("TABLES FOUND:", len(tables))

    if len(tables) < 2:
        return []

    t1 = tables[0]["team"]
    t2 = tables[1]["team"]

    rows = []

    for i, t in enumerate(tables[:2]):
        team = t["team"]
        opp = t2 if i == 0 else t1

        players = parse_players(t["table"])

        if not players:
            print("Skipping bad table")
            return []

        team_score = scores.get(team, 0)
        opp_score = scores.get(opp, 0)

        for p in players:
            rows.append({
                "match_id": match_id,
                "season": YEAR,
                "round": header["round"],
                "player": p["player"],
                "played_for": team,
                "played_against": opp,
                **p,
                "date_iso": header["date_iso"],
                "venue": header["venue"],
                "crowd": header["crowd"],
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

    with open(SEASON_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(all_rows, f, indent=2)

    players = build_players(all_rows)

    with open(PLAYERS_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(players, f, indent=2)

    print("DONE")


if __name__ == "__main__":
    main()
