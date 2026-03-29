import csv
import io
import json
import requests
from pathlib import Path

print("REBUILDING TENNIS HISTORY (CORRECT STRUCTURE)")

BASE = Path("docs/data/tennis")
SEASONS = BASE / "seasons"
MATCHES = BASE / "matches"

SEASONS.mkdir(parents=True, exist_ok=True)
MATCHES.mkdir(parents=True, exist_ok=True)

ATP = "https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_matches_{year}.csv"
WTA = "https://raw.githubusercontent.com/JeffSackmann/tennis_wta/master/wta_matches_{year}.csv"

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})


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
    tournament = row.get("tourney_name", "").strip()
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
        "tourney_id": row.get("tourney_id", ""),
    }

    # FULL STAT FIELDS (CRITICAL)
    stats = [
        "w_ace","w_df","w_svpt","w_1stIn","w_1stWon","w_2ndWon",
        "w_SvGms","w_bpSaved","w_bpFaced",
        "l_ace","l_df","l_svpt","l_1stIn","l_1stWon","l_2ndWon",
        "l_SvGms","l_bpSaved","l_bpFaced"
    ]

    for s in stats:
        m[s] = safe_int(row.get(s))

    return m


def fetch(url):
    r = session.get(url)
    if r.status_code != 200:
        return []
    return list(csv.DictReader(io.StringIO(r.text)))


for year in range(1968, 2025):
    print(f"YEAR {year}")

    matches = []

    for gender, url in [("M", ATP), ("F", WTA)]:
        rows = fetch(url.format(year=year))

        for r in rows:
            m = build_match(r, gender)
            if m:
                matches.append(m)

    # save EXACTLY how your site expects
    (SEASONS / f"{year}.json").write_text(json.dumps(matches, indent=2))
    (MATCHES / f"{year}.json").write_text(json.dumps(matches, indent=2))

    print(f"Saved {year}: {len(matches)} matches")

print("DONE")
