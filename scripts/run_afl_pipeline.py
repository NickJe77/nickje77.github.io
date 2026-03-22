import json
import re
import shutil
import unicodedata
from pathlib import Path

import requests
from bs4 import BeautifulSoup

print("AFL FULL PIPELINE — FINAL (ALL SEASONS + PLAYERS)")

BASE = "https://www.footywire.com"
HEADERS = {"User-Agent": "Mozilla/5.0"}
SEASON = 2026

DATA_DIR = Path("docs/data/afl")
OUTPUT = DATA_DIR / f"afl_{SEASON}.json"
PLAYERS_DIR = DATA_DIR / "players"
PLAYERS_INDEX = DATA_DIR / "players.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------
# HELPERS
# -----------------------------
def clean(text):
    return re.sub(r"\s+", " ", (text or "")).strip()

def to_int(x):
    try:
        return int(x)
    except:
        try:
            return int(float(x))
        except:
            return 0

def slugify(name):
    name = unicodedata.normalize("NFD", name)
    name = name.encode("ascii", "ignore").decode("utf-8")
    name = name.lower()
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"\s+", "-", name)
    return name.strip("-")

# -----------------------------
# SCRAPER
# -----------------------------
def get_links():
    links = set()

    for rnd in range(0, 31):
        url = f"{BASE}/afl/footy/ft_match_list?year={SEASON}&round={rnd}"

        try:
            res = requests.get(url, headers=HEADERS, timeout=30)
            res.raise_for_status()
        except:
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


def get_round(soup):
    txt = clean(soup.get_text(" ", strip=True))
    m = re.search(r"Round\s+(\d+)", txt)
    return int(m.group(1)) if m else None


def parse_title_teams(title):
    title = clean(title.replace("AFL Match Statistics :", ""))

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


def scrape():
    all_data = []

    for url in get_links():
        print("→", url)

        try:
            res = requests.get(url, headers=HEADERS, timeout=30)
            res.raise_for_status()
        except:
            continue

        soup = BeautifulSoup(res.text, "html.parser")

        title = soup.find("title").text
        team1, team2 = parse_title_teams(title)

        if not team1:
            continue

        round_num = get_round(soup)

        rows = soup.find_all("tr")
        current_team = None

        for tr in rows:
            text = clean(tr.get_text(" ", strip=True))

            # Detect team section
            m = re.match(r"^(.*?) Match Statistics \(Sorted by Disposals\)", text)
            if m:
                t = clean(m.group(1))
                if t in (team1, team2):
                    current_team = t
                else:
                    current_team = None
                continue

            if not current_team:
                continue

            cols = tr.find_all("td", recursive=False)
            if len(cols) < 18:
                continue

            link = cols[0].find("a")
            if not link:
                continue

            name = clean(link.text)
            opponent = team2 if current_team == team1 else team1

            all_data.append({
                "player": name,
                "played_for": current_team,
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

    return all_data


# -----------------------------
# PLAYERS BUILDER
# -----------------------------
def build_players(rows):

    if PLAYERS_DIR.exists():
        shutil.rmtree(PLAYERS_DIR)

    PLAYERS_DIR.mkdir(parents=True, exist_ok=True)

    players = {}

    for r in rows:
        name = clean(r["player"])
        slug = slugify(name)

        if slug not in players:
            players[slug] = {
                "player": name,
                "slug": slug,
                "games": [],
                "_seen": set()
            }

        key = (
            name,
            r["season"],
            r["round"],
            r["played_for"],
            r["played_against"],
            r["K"], r["HB"], r["D"]
        )

        if key in players[slug]["_seen"]:
            continue

        players[slug]["_seen"].add(key)

        players[slug]["games"].append({
            "season": r["season"],
            "round": r["round"],
            "team": r["played_for"],
            "opponent": r["played_against"],
            "K": r["K"],
            "HB": r["HB"],
            "D": r["D"],
            "M": r["M"],
            "G": r["G"],
            "B": r["B"],
            "T": r["T"],
            "HO": r["HO"],
            "GA": r["GA"],
            "I50": r["I50"],
            "CL": r["CL"],
            "CG": r["CG"],
            "R50": r["R50"],
            "FF": r["FF"],
            "FA": r["FA"],
            "AF": r["AF"],
            "SC": r["SC"]
        })

    index = []

    for slug, p in players.items():

        games = sorted(p["games"], key=lambda g: (g["season"], g["round"] or 999))

        seasons = sorted({g["season"] for g in games})
        teams = list(dict.fromkeys([g["team"] for g in games]))

        out = {
            "player": p["player"],
            "slug": slug,
            "seasons": seasons,
            "teams": teams,
            "games": games
        }

        with open(PLAYERS_DIR / f"{slug}.json", "w") as f:
            json.dump(out, f, indent=2)

        index.append({
            "player": p["player"],
            "slug": slug,
            "seasons": seasons,
            "teams": teams
        })

    with open(PLAYERS_INDEX, "w") as f:
        json.dump(index, f, indent=2)


# -----------------------------
# RUN PIPELINE
# -----------------------------
print("\n--- SCRAPING CURRENT SEASON ---")
rows_2026 = scrape()

print("2026 ROWS:", len(rows_2026))

with open(OUTPUT, "w") as f:
    json.dump(rows_2026, f, indent=2)

print("WROTE:", OUTPUT)

print("\n--- LOADING ALL SEASONS ---")
all_rows = []

for file in DATA_DIR.glob("afl_*.json"):
    print("Loading:", file)

    try:
        with open(file, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                all_rows.extend(data)
    except:
        continue

print("TOTAL PLAYER SOURCE ROWS:", len(all_rows))

print("\n--- BUILDING PLAYERS ---")
build_players(all_rows)

print("DONE ✅")
