import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import re

print("AFL SCRAPER — BULLETPROOF VERSION")

BASE = "https://www.footywire.com"
HEADERS = {"User-Agent": "Mozilla/5.0"}

SEASON = 2026
OUTPUT = Path(f"docs/data/afl/afl_{SEASON}.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)


def to_int(x):
    try:
        return int(x.strip())
    except:
        return 0


def clean(s):
    return re.sub(r"\s+", " ", (s or "")).strip()


# -----------------------------
# GET MATCH LINKS
# -----------------------------
def get_links():
    links = set()

    for rnd in range(0, 31):
        url = f"{BASE}/afl/footy/ft_match_list?year={SEASON}&round={rnd}"

        res = requests.get(url, headers=HEADERS)
        if res.status_code != 200:
            continue

        soup = BeautifulSoup(res.text, "html.parser")

        for a in soup.find_all("a", href=True):
            href = a["href"]

            if "ft_match_statistics" not in href:
                continue

            if href.startswith("/"):
                href = BASE + href
            elif not href.startswith("http"):
                href = BASE + "/afl/footy/" + href

            links.add(href)

    return sorted(links)


# -----------------------------
# GET ROUND
# -----------------------------
def get_round(soup):
    txt = soup.get_text(" ", strip=True)
    m = re.search(r"Round\s+(\d+)", txt)
    return int(m.group(1)) if m else None


# -----------------------------
# FIND PLAYER TABLES
# -----------------------------
def get_player_tables(soup):

    tables = soup.find_all("table")
    valid = []

    for t in tables:

        txt = t.get_text()

        # must contain stat headers
        if not ("K" in txt and "HB" in txt and "D" in txt):
            continue

        # must contain player links
        if not t.find("a"):
            continue

        valid.append(t)

    # keep only the 2 biggest (actual player tables)
    valid = sorted(valid, key=lambda t: len(t.find_all("tr")), reverse=True)

    return valid[:2]


# -----------------------------
# GET TEAMS FROM TITLE
# -----------------------------
def get_teams(title):

    title = title.replace("AFL Match Statistics :", "").strip()

    if " def " in title:
        a, b = title.split(" def ")
        return clean(a), clean(b.split(" at ")[0])

    if " defeats " in title:
        a, b = title.split(" defeats ")
        return clean(a), clean(b.split(" at ")[0])

    if " defeated by " in title:
        a, b = title.split(" defeated by ")
        return clean(b.split(" at ")[0]), clean(a)

    return None, None


# -----------------------------
# PARSE MATCH
# -----------------------------
def parse_match(url):

    print("→", url)

    soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "html.parser")

    title = soup.find("title").text
    team1, team2 = get_teams(title)

    if not team1:
        print("⚠️ No teams")
        return []

    round_num = get_round(soup)

    tables = get_player_tables(soup)

    if len(tables) < 2:
        print("⚠️ No player tables")
        return []

    data = []

    # 🔥 IMPORTANT: tables are not guaranteed order
    # we split rows evenly to determine team

    table_rows = [t.find_all("tr") for t in tables]

    # assign teams based on first appearance (safe)
    team_map = {
        0: team1,
        1: team2
    }

    for i, rows in enumerate(table_rows):

        played_for = team_map[i]
        played_against = team2 if played_for == team1 else team1

        for r in rows:
            cols = r.find_all("td")

            if len(cols) < 18:
                continue

            link = cols[0].find("a")
            if not link:
                continue

            name = clean(link.text)

            data.append({
                "player": name,
                "played_for": played_for,
                "played_against": played_against,
                "season": SEASON,
                "round": round_num,

                "K": to_int(cols[1].text),
                "HB": to_int(cols[2].text),
                "D": to_int(cols[3].text),
                "M": to_int(cols[4].text),
                "G": to_int(cols[5].text),
                "B": to_int(cols[6].text),
                "T": to_int(cols[7].text),
                "HO": to_int(cols[8].text),
                "GA": to_int(cols[9].text),
                "I50": to_int(cols[10].text),
                "CL": to_int(cols[11].text),
                "CG": to_int(cols[12].text),
                "R50": to_int(cols[13].text),
                "FF": to_int(cols[14].text),
                "FA": to_int(cols[15].text),
                "AF": to_int(cols[16].text),
                "SC": to_int(cols[17].text)
            })

    return data


# -----------------------------
# RUN
# -----------------------------
all_data = []

for link in get_links():
    try:
        all_data.extend(parse_match(link))
    except Exception as e:
        print("ERROR:", e)

print("TOTAL ROWS:", len(all_data))

with open(OUTPUT, "w") as f:
    json.dump(all_data, f, indent=2)

print("DONE")
