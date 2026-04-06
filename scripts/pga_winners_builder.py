import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import time
import re

print("PGA BUILDER (MAJORS + PLAYERS)")

BASE_DIR = Path("docs/data/golf")
PLAYERS_DIR = BASE_DIR / "players"

BASE_DIR.mkdir(parents=True, exist_ok=True)
PLAYERS_DIR.mkdir(parents=True, exist_ok=True)

OUT_FILE = BASE_DIR / "pga_winners.json"
PLAYERS_INDEX = BASE_DIR / "players.json"

HEADERS = {"User-Agent": "Mozilla/5.0"}

START_YEAR = 1968
END_YEAR = 2026


# ---------------------------
# MAJORS LIST
# ---------------------------
MAJORS = [
    "masters",
    "u.s. open",
    "the open",
    "open championship",
    "pga championship"
]


def is_major(event):
    e = event.lower()
    return any(m in e for m in MAJORS)


def slugify(name):
    name = name.lower()
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"\s+", "-", name)
    return name.strip("-")


def clean_text(text):
    return text.replace("\n", "").replace("\xa0", " ").strip()


def get_page(year):
    url = f"https://en.wikipedia.org/wiki/{year}_PGA_Tour"
    r = requests.get(url, headers=HEADERS, timeout=20)

    if r.status_code != 200:
        print("Failed:", year)
        return None

    return BeautifulSoup(r.text, "html.parser")


def parse_tables(soup, year):
    tables = soup.find_all("table", {"class": "wikitable"})
    rows = []

    for table in tables:
        headers = [clean_text(th.text).lower() for th in table.find_all("th")]

        winner_idx = None
        event_idx = None

        for i, h in enumerate(headers):
            if "winner" in h:
                winner_idx = i
            if "tournament" in h or "event" in h:
                event_idx = i

        if winner_idx is None or event_idx is None:
            continue

        for row in table.find_all("tr")[1:]:
            cols = [clean_text(c.text) for c in row.find_all(["td", "th"])]

            if len(cols) <= max(winner_idx, event_idx):
                continue

            winner = cols[winner_idx]
            event = cols[event_idx]

            # skip garbage
            if "$" in winner or winner.replace(",", "").isdigit():
                continue

            if not winner or not event:
                continue

            rows.append({
                "tour": "pga",
                "year": year,
                "date": "",
                "event": event,
                "winner": winner,
                "major": is_major(event),
                "score": "",
                "venue": "",
                "country": "",
                "url": f"https://en.wikipedia.org/wiki/{year}_PGA_Tour"
            })

    return rows


# ---------------------------
# BUILD DATA
# ---------------------------
all_rows = []
players = {}

for year in range(START_YEAR, END_YEAR + 1):
    print(f"YEAR {year}")

    soup = get_page(year)
    if not soup:
        continue

    rows = parse_tables(soup, year)
    print("  found:", len(rows))

    for r in rows:
        all_rows.append(r)

        name = r["winner"]
        slug = slugify(name)

        if slug not in players:
            players[slug] = {
                "name": name,
                "slug": slug,
                "wins": 0,
                "majors": 0,
                "years": set(),
                "events": []
            }

        players[slug]["wins"] += 1
        if r["major"]:
            players[slug]["majors"] += 1

        players[slug]["years"].add(r["year"])
        players[slug]["events"].append(r)

    time.sleep(0.3)


# ---------------------------
# CLEAN PLAYERS
# ---------------------------
players_list = []

for slug, p in players.items():
    p["years"] = sorted(list(p["years"]))
    p["events"].sort(key=lambda x: x["year"], reverse=True)

    # save individual player file
    with open(PLAYERS_DIR / f"{slug}.json", "w") as f:
        json.dump(p, f, indent=2)

    players_list.append({
        "name": p["name"],
        "slug": slug,
        "wins": p["wins"],
        "majors": p["majors"]
    })


# sort players by wins
players_list.sort(key=lambda x: x["wins"], reverse=True)


# ---------------------------
# SAVE FILES
# ---------------------------
with open(OUT_FILE, "w") as f:
    json.dump(all_rows, f, indent=2)

with open(PLAYERS_INDEX, "w") as f:
    json.dump(players_list, f, indent=2)

print("DONE")
print("Players:", len(players_list))
print("Tournaments:", len(all_rows))
