import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import re

print("AFL SCRAPER — TRUE FINAL FIX")

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
# GET LINKS
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
# GET TEAMS FROM TABS
# -----------------------------
def get_teams(soup):
    teams = []

    for a in soup.find_all("a"):
        txt = clean(a.get_text())

        if "Player Stats" in txt:
            teams.append(txt.replace("Player Stats", "").strip())

    if len(teams) >= 2:
        return teams[0], teams[1]

    return None, None


# -----------------------------
# GET ROUND
# -----------------------------
def get_round(soup):
    txt = soup.get_text(" ", strip=True)

    m = re.search(r"Round\s+(\d+)", txt)
    if m:
        return int(m.group(1))

    return None


# -----------------------------
# GET CORRECT PLAYER TABLES
# -----------------------------
def get_player_tables(soup):

    tables = soup.find_all("table")
    result = []

    for t in tables:
        txt = clean(t.get_text())

        # 🔥 THIS IS THE KEY FILTER
        if "Match Statistics (Sorted by Disposals)" in txt:
            result.append(t)

    return result[:2]


# -----------------------------
# PARSE MATCH
# -----------------------------
def parse_match(url):

    print("→", url)

    soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "html.parser")

    team1, team2 = get_teams(soup)

    if not team1:
        print("⚠️ No teams found")
        return []

    round_num = get_round(soup)

    tables = get_player_tables(soup)

    if len(tables) < 2:
        print("⚠️ No player tables")
        return []

    data = []

    teams = [team1, team2]

    for i in range(2):

        played_for = teams[i]
        played_against = teams[1 - i]

        rows = tables[i].find_all("tr")

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
