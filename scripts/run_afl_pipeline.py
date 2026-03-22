import json
import re
from pathlib import Path
from collections import defaultdict

import requests
from bs4 import BeautifulSoup

DATA_DIR = Path("docs/data/afl")
PLAYERS_DIR = DATA_DIR / "players"
PLAYERS_JSON = DATA_DIR / "players.json"

SEASON = 2026

OUTPUT = DATA_DIR / f"afl_{SEASON}.json"

PLAYERS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

BASE = "https://www.footywire.com"
HEADERS = {"User-Agent": "Mozilla/5.0"}


# -------------------------------
# SCRAPER (MINIMAL ADD)
# -------------------------------
def clean(text):
    return re.sub(r"\s+", " ", (text or "")).strip()

def to_int(text):
    try:
        return int(clean(text))
    except:
        return 0

def get_round(soup):
    txt = soup.get_text(" ", strip=True).lower()
    m = re.search(r"round\s+(\d+)", txt)
    return int(m.group(1)) if m else None

def get_links():
    links = set()

    for rnd in range(0, 31):
        url = f"{BASE}/afl/footy/ft_match_list?year={SEASON}&round={rnd}"
        try:
            res = requests.get(url, headers=HEADERS, timeout=30)
            soup = BeautifulSoup(res.text, "html.parser")
        except:
            continue

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

def parse_match(url, match_counter):
    try:
        res = requests.get(url, headers=HEADERS, timeout=30)
        soup = BeautifulSoup(res.text, "html.parser")
    except:
        return []

    title = soup.find("title")
    if not title:
        return []

    text = clean(title.text)

    if " def " not in text:
        return []

    team_a, team_b = text.split(" def ", 1)
    team_b = team_b.split(" at ")[0]

    round_num = get_round(soup)
    round_label = f"Round {round_num}" if round_num else f"Round {match_counter}"

    match_id = f"{SEASON}_{match_counter:04d}"

    rows = soup.find_all("tr")
    current_team = None
    data = []

    for tr in rows:
        txt = clean(tr.get_text(" ", strip=True))

        m = re.match(r"^(.*?) Match Statistics", txt)
        if m:
            current_team = clean(m.group(1))
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
        opponent = team_b if current_team == team_a else team_a

        row = {
            "match_id": match_id,
            "player": name,
            "played_for": current_team,
            "played_against": opponent,
            "season": SEASON,
            "round": round_label,
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
            "SC": to_int(cols[17].text),
        }

        data.append(row)

    return data


def scrape():
    print("SCRAPING 2026...")

    all_rows = []
    match_counter = 0

    for link in get_links():
        match_counter += 1
        all_rows.extend(parse_match(link, match_counter))

    OUTPUT.write_text(json.dumps(all_rows, indent=2))
    print("SCRAPER DONE:", len(all_rows))


# -------------------------------
# PLAYER PIPELINE (UNCHANGED)
# -------------------------------
def load_rows():
    return json.loads(OUTPUT.read_text())


def build_players(rows):
    players = {}

    for r in rows:
        name = r.get("player")
        if not name:
            continue

        if name not in players:
            players[name] = {
                "name": name,
                "games": [],
                "career": defaultdict(int),
            }

        entry = {
            "season": r.get("season"),
            "round": r.get("round"),
            "team": r.get("played_for"),
            "opponent": r.get("played_against"),
            "match_id": r.get("match_id"),
            "stats": r
        }

        players[name]["games"].append(entry)

        for k, v in r.items():
            if isinstance(v, (int, float)):
                players[name]["career"][k] += v

    return players


def save_players(players):
    summary = []

    for name, p in players.items():
        slug = name.lower().replace(" ", "-")

        (PLAYERS_DIR / f"{slug}.json").write_text(json.dumps({
            "name": name,
            "career": dict(p["career"]),
            "games": p["games"]
        }, indent=2))

        summary.append({
            "name": name,
            "slug": slug,
            "games": len(p["games"])
        })

    PLAYERS_JSON.write_text(json.dumps(summary, indent=2))


# -------------------------------
# MAIN
# -------------------------------
def main():
    scrape()  # 🔥 THIS WAS MISSING

    rows = load_rows()
    players = build_players(rows)
    save_players(players)

    print("DONE")


if __name__ == "__main__":
    main()
