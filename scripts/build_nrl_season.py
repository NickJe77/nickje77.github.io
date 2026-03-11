import json
import requests
from pathlib import Path

SEASON = 2026

NRL_INDEX = Path("docs/data/nrl/index.json")
MATCH_DIR = Path(f"docs/data/nrl/matches/{SEASON}")
SEASON_FILE = Path(f"docs/data/nrl/seasons/{SEASON}.json")

MATCH_DIR.mkdir(parents=True, exist_ok=True)
SEASON_FILE.parent.mkdir(parents=True, exist_ok=True)

URL = f"https://www.nrl.com/draw/data?competition=111&season={SEASON}"

print("Downloading NRL matches...")

headers = {"User-Agent": "Mozilla/5.0"}

r = requests.get(URL, headers=headers, timeout=30)

if r.status_code != 200:
    print("Download failed:", r.status_code)
    raise SystemExit(1)

data = r.json()

fixtures = data.get("fixtures", [])
print("Fixtures detected:", len(fixtures))

all_rows = []
match_ids = []

for m in fixtures:
    home_team = m.get("homeTeam", {}).get("nickName", "")
    away_team = m.get("awayTeam", {}).get("nickName", "")

    if not home_team or not away_team:
        continue

    round_title = m.get("roundTitle", "")
    round_num = 0
    if round_title.startswith("Round "):
        try:
            round_num = int(round_title.replace("Round ", "").strip())
        except:
            round_num = 0

    date_iso = ""
    kick = m.get("clock", {}).get("kickOffTimeLong", "")
    if kick:
        date_iso = kick[:10]

    venue = m.get("venue", "") or ""

    home_points = m.get("homeScore", 0)
    away_points = m.get("awayScore", 0)

    game_id = f"{SEASON}R{round_num:02d}{home_team[:3]}{away_team[:3]}".upper()

    match_ids.append(game_id)

    row = {
        "season": SEASON,
        "match_id": game_id,
        "date_iso": date_iso,
        "venue": venue,
        "home_team": home_team,
        "away_team": away_team,
        "home_points": home_points,
        "away_points": away_points
    }

    all_rows.append(row)

    match_file = MATCH_DIR / f"{game_id}.json"
    with open(match_file, "w", encoding="utf-8") as f:
        json.dump([row], f, indent=2, ensure_ascii=False)

# rebuild season file every run
all_rows.sort(key=lambda x: (x.get("date_iso", ""), x.get("match_id", "")))

with open(SEASON_FILE, "w", encoding="utf-8") as f:
    json.dump(all_rows, f, indent=2, ensure_ascii=False)

print("Season file rebuilt:", SEASON_FILE)

# update main NRL index.json so season page buttons work
if NRL_INDEX.exists():
    try:
        with open(NRL_INDEX, "r", encoding="utf-8") as f:
            index = json.load(f)
    except:
        index = {}
else:
    index = {}

if "seasons" not in index or not isinstance(index["seasons"], list):
    index["seasons"] = []

if SEASON not in index["seasons"]:
    index["seasons"].append(SEASON)

index["seasons"] = sorted(set(index["seasons"]))

with open(NRL_INDEX, "w", encoding="utf-8") as f:
    json.dump(index, f, indent=2, ensure_ascii=False)

print("Index updated:", NRL_INDEX)
print("Match files written:", len(match_ids))
print("Update complete")
