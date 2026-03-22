import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import re
from datetime import datetime

print("RUNNING AFL SCRAPER 2026")

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
        print(f"Checking Round {rnd}...")

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

    links = sorted(links)
    print("TOTAL MATCHES:", len(links))
    return links


# -----------------------------
# PARSE TITLE TEAMS
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
# MATCH
# -----------------------------
def parse_match(url):
    print("→", url)

    soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "html.parser")

    title = soup.find("title").text
    team1, team2 = parse_title(title)

    if not team1:
        print("⚠️ bad title")
        return []

    round_num = get_round(soup)
    print("ROUND:", round_num)

    tables = soup.find_all("table")
    stat_tables = []

    for t in tables:
        txt = t.get_text()
        if "K" in txt and "HB" in txt and "D" in txt:
            stat_tables.append(t)

    if len(stat_tables) < 2:
        return []

    data = []

    for i in range(2):
        rows = stat_tables[i].find_all("tr")

        for r in rows:
            cols = r.find_all("td")
            if len(cols) < 18:
                continue

            link = cols[0].find("a")
            if not link:
                continue

            name = clean(link.text)

            played_for = team1 if i == 0 else team2
            played_against = team2 if i == 0 else team1

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

print("WRITTEN:", OUTPUT)
print("UPDATED:", datetime.utcnow())
