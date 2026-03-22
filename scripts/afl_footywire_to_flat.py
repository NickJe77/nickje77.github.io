import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import re

print("AFL SCRAPER — FINAL WORKING VERSION (TEAM FIX CONFIRMED)")

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
    result = []

    for t in tables:
        txt = t.get_text()

        if "Match Statistics (Sorted by Disposals)" in txt:
            result.append(t)

    return result[:2]


# -----------------------------
# EXTRACT TEAM FROM TABLE (🔥 FINAL FIX)
# -----------------------------
def extract_team_from_table(table):

    first_row = table.find("tr")
    if not first_row:
        return None

    txt = first_row.get_text(" ", strip=True)

    m = re.search(r"^(.*?) Match Statistics", txt)
    if m:
        return m.group(1).strip()

    return None


# -----------------------------
# PARSE MATCH
# -----------------------------
def parse_match(url):

    print("→", url)

    soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "html.parser")

    round_num = get_round(soup)

    tables = get_player_tables(soup)

    if len(tables) < 2:
        print("⚠️ Could not find player tables")
        return []

    teams = []

    for table in tables:
        team = extract_team_from_table(table)

        if not team:
            print("⚠️ Failed to extract team")
            return []

        teams.append(team)

    data = []

    for i, table in enumerate(tables):

        played_for = teams[i]
        played_against = teams[1 - i]

        rows = table.find_all("tr")

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
