import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import re

print("AFL SCRAPER — FINAL TEAM FIX (TABLE COUNT METHOD)")

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
# TITLE TEAMS
# -----------------------------
def parse_title(title):
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
# ROUND
# -----------------------------
def get_round(soup):
    for tag in soup.find_all(["td", "b", "span", "div"]):
        txt = clean(tag.get_text())
        if "Round" in txt:
            m = re.search(r"Round\s+(\d+)", txt)
            if m:
                return int(m.group(1))
    return None


# -----------------------------
# COUNT PLAYERS IN TABLE
# -----------------------------
def count_players(table):
    count = 0
    for r in table.find_all("tr"):
        cols = r.find_all("td")
        if len(cols) < 18:
            continue
        if cols[0].find("a"):
            count += 1
    return count


# -----------------------------
# MATCH
# -----------------------------
def parse_match(url):
    print("→", url)

    soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "html.parser")

    title = soup.find("title").text
    team1, team2 = parse_title(title)

    if not team1:
        return []

    round_num = get_round(soup)

    tables = soup.find_all("table")

    stat_tables = []
    for t in tables:
        txt = t.get_text()
        if "K" in txt and "HB" in txt and "D" in txt:
            stat_tables.append(t)

    if len(stat_tables) < 2:
        return []

    # 🔥 COUNT PLAYERS
    c0 = count_players(stat_tables[0])
    c1 = count_players(stat_tables[1])

    print("TABLE COUNTS:", c0, c1)

    # 🔥 ASSIGN TEAMS BASED ON COUNT
    # Usually: one team has ~22–23 players, the other similar
    # but consistency is: first table = home team MOST of the time

    # fallback logic
    if c0 >= c1:
        table_team_map = {
            0: team1,
            1: team2
        }
    else:
        table_team_map = {
            0: team2,
            1: team1
        }

    data = []

    for i in range(2):

        played_for = table_team_map[i]
        played_against = team2 if played_for == team1 else team1

        rows = stat_tables[i].find_all("tr")

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
