import json
import requests
from pathlib import Path

SEASON = 2026

BASE = Path("docs/data/nrl")

INDEX_FILE = BASE / "index.json"
MATCH_DIR = BASE / "matches" / str(SEASON)
SEASON_FILE = BASE / "seasons" / f"{SEASON}.json"

MATCH_DIR.mkdir(parents=True, exist_ok=True)
SEASON_FILE.parent.mkdir(parents=True, exist_ok=True)

URL = f"https://www.nrl.com/draw/data?competition=111&season={SEASON}&round=all"

print("Downloading NRL matches...")

headers = {"User-Agent": "Mozilla/5.0"}

r = requests.get(URL, headers=headers, timeout=30)

if r.status_code != 200:
    print("Download failed:", r.status_code)
    raise SystemExit(1)

data = r.json()

fixtures = data.get("fixtures", [])

print("Fixtures detected:", len(fixtures))

rows = []

for m in fixtures:

    home = m.get("homeTeam", {}).get("nickName")
    away = m.get("awayTeam", {}).get("nickName")

    if not home or not away:
        continue

    round_title = m.get("roundTitle", "")

    if "Opening" in round_title:
        round_num = 1
    elif round_title.startswith("Round"):
        try:
            round_num = int(round_title.split()[1])
        except:
            round_num = 0
    else:
        round_num = 0

    kickoff = m.get("clock", {}).get("kickOffTimeLong", "")
    date_iso = kickoff[:10] if kickoff else ""

    venue = m.get("venue", "")

    home_pts = m.get("homeScore", 0)
    away_pts = m.get("awayScore", 0)

    match_id = f"{SEASON}R{round_num:02d}{home[:3]}{away[:3]}".upper()

    row = {
        "season": SEASON,
        "match_id": match_id,
        "date_iso": date_iso,
        "venue": venue,
        "home_team": home,
        "away_team": away,
        "home_points": home_pts,
        "away_points": away_pts
    }

    rows.append(row)

    match_file = MATCH_DIR / f"{match_id}.json"

    with open(match_file, "w", encoding="utf-8") as f:
        json.dump([row], f, indent=2)

rows.sort(key=lambda x: (x["date_iso"], x["match_id"]))

with open(SEASON_FILE, "w", encoding="utf-8") as f:
    json.dump(rows, f, indent=2)

print("Season file rebuilt:", SEASON_FILE)

if INDEX_FILE.exists():
    with open(INDEX_FILE) as f:
        index = json.load(f)
else:
    index = {}

if "seasons" not in index:
    index["seasons"] = []

if SEASON not in index["seasons"]:
    index["seasons"].append(SEASON)

index["seasons"] = sorted(index["seasons"])

with open(INDEX_FILE, "w") as f:
    json.dump(index, f, indent=2)

print("Index updated")

print("Matches written:", len(rows))
print("Update complete")
