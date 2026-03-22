import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import re

print("AFL SCRAPER — FINAL (TABLE HEADER TEAM DETECTION)")

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
# LINKS
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
# ROUND
# -----------------------------
def get_round(soup):
    txt = soup.get_text(" ", strip=True)
    m = re.search(r"Round\s+(\d+)", txt)
    if m:
        return int(m.group(1))
    return None


# -----------------------------
# GET PLAYER TABLES WITH TEAM
# -----------------------------
def get_player_tables(soup):

    tables = soup.find_all("table")
    result = []

    for t in tables:

        txt = clean(t.get_text())

        if "Match Statistics (Sorted by Disposals)" not in txt:
            continue

        # 🔥 EXTRACT TEAM NAME FROM TABLE TEXT
        m = re.search(r"^(.*?) Match Statistics", txt)
        if not m:
            continue

        team = clean(m.group(1))

        result.append((t, team))

    return result


# -----------------------------
# PARSE MATCH
# -----------------------------
def parse_match(url):

    print("→", url)

    soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "html.parser")

    round_num = get_round(soup)

    tables = get_player_tables(soup)

    if len(tables) < 2:
        print("⚠️ No valid player tables")
        return []

    data = []

    # determine opponents
    teams = [tables[0][1], tables[1][1]]

    for table, team in tables[:2]:

        opponent = teams[1] if team == teams[0] else teams[0]

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
                "played_for": team,
                "played_against": opponent,
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
