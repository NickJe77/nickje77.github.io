import json
import requests
from pathlib import Path

print("NRL UPDATE FINAL")

SEASON = 2026

BASE = Path("docs/data/nrl")
SEASON_FILE = BASE / "seasons" / f"{SEASON}.json"
INDEX_FILE = BASE / "index.json"

BASE.mkdir(parents=True, exist_ok=True)
SEASON_FILE.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}


def fetch_json(url):

    r = requests.get(url, headers=HEADERS, timeout=30)

    if r.status_code != 200:
        return None

    try:
        return r.json()
    except:
        return None


def get_round(round_name):

    url = f"https://www.nrl.com/draw/data?competition=111&season={SEASON}&round={round_name}"

    data = fetch_json(url)

    if not data:
        return []

    return data.get("fixtures", [])


print("Downloading fixtures...")

fixtures = []
fixtures.extend(get_round("opening"))
fixtures.extend(get_round("all"))

print("Raw fixtures detected:", len(fixtures))

# Deduplicate fixtures
dedup = {}

for m in fixtures:

    match_id = m.get("matchId") or m.get("id")

    if match_id:
        dedup[str(match_id)] = m
    else:
        key = f"{m.get('roundTitle','')}|{m.get('homeTeam',{}).get('nickName','')}|{m.get('awayTeam',{}).get('nickName','')}"
        dedup[key] = m

fixtures = list(dedup.values())

print("Unique fixtures detected:", len(fixtures))

rows = []

for m in fixtures:

    home = m.get("homeTeam", {}).get("nickName")
    away = m.get("awayTeam", {}).get("nickName")

    if not home or not away:
        continue

    match_id = m.get("matchId") or m.get("id")

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

    home_points = m.get("homeScore", 0)
    away_points = m.get("awayScore", 0)

    if not match_id:
        match_id = f"{SEASON}R{round_num:02d}{home[:3]}{away[:3]}".upper()

    row = {

        "season": SEASON,
        "match_id": str(match_id),
        "date_iso": date_iso,
        "venue": venue,
        "home_team": home,
        "away_team": away,
        "home_points": home_points,
        "away_points": away_points

    }

    rows.append(row)


rows.sort(key=lambda x: (x["date_iso"], x["match_id"]))

print("Rows prepared:", len(rows))


if not rows:
    print("No rows found. Existing season file left untouched.")
    raise SystemExit(1)


with open(SEASON_FILE, "w") as f:
    json.dump(rows, f, indent=2)

print("Season written:", SEASON_FILE)


# Update index
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
print("Update complete")
