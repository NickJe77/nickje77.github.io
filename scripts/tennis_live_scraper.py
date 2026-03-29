import requests
import csv
import io
import json
from pathlib import Path

print("LIVE TENNIS SCRAPER (WORKING SOURCE)")

BASE = Path("docs/data/tennis")
MATCHES = BASE / "matches"
SEASONS = BASE / "seasons"

MATCHES.mkdir(parents=True, exist_ok=True)
SEASONS.mkdir(parents=True, exist_ok=True)

YEARS = [2025, 2026]

ATP = "https://tennisabstract.com/cgi-bin/atp_matches_{year}.csv"
WTA = "https://tennisabstract.com/cgi-bin/wta_matches_{year}.csv"


def parse_date(d):
    if d and len(d) == 8:
        return f"{d[:4]}-{d[4:6]}-{d[6:8]}"
    return ""


def slug(s):
    return "".join(c.lower() if c.isalnum() else "-" for c in s).strip("-")


def safe_int(v):
    try:
        return int(float(v))
    except:
        return 0


def build_match(row, gender):
    winner = row.get("winner_name", "").strip()
    loser = row.get("loser_name", "").strip()

    if not winner or not loser:
        return None

    date = parse_date(row.get("tourney_date"))
    tournament = row.get("tourney_name", "")
    rnd = row.get("round", "")
    score = row.get("score", "")
    surface = row.get("surface", "")

    match_id = f"{date[:4]}_{gender.lower()}_{date}_{slug(tournament)}_{rnd.lower()}_{slug(winner)}_{slug(loser)}"

    m = {
        "match_id": match_id,
        "date": date,
        "tournament": tournament,
        "surface": surface,
        "round": rnd,
        "player1": winner,
        "player2": loser,
        "winner": winner,
        "loser": loser,
        "score": score,
        "gender": gender,
        "best_of": safe_int(row.get("best_of")),
        "draw_size": safe_int(row.get("draw_size")),
        "minutes": safe_int(row.get("minutes")),
        "tourney_level": row.get("tourney_level", ""),
        "tourney_id": row.get("tourney_id", "")
    }

    return m


def fetch(url):
    r = requests.get(url)
    if r.status_code != 200:
        return []
    return list(csv.DictReader(io.StringIO(r.text)))


for year in YEARS:
    print(f"Processing {year}")

    matches = []

    for gender, url in [("M", ATP), ("F", WTA)]:
        rows = fetch(url.format(year=year))

        if not rows:
            print(f"{year} no data for {gender}")
            continue

        for r in rows:
            m = build_match(r, gender)
            if m:
                matches.append(m)

    (MATCHES / f"{year}.json").write_text(json.dumps(matches, indent=2))
    (SEASONS / f"{year}.json").write_text(json.dumps(matches, indent=2))

    print(f"{year}: {len(matches)} matches saved")

print("DONE")
