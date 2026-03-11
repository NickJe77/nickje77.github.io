import json
import requests
from pathlib import Path
from datetime import datetime, timezone

print("NRL UPDATE SAFE MODE")

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
    except Exception:
        return None

def get_round(round_name):
    url = f"https://www.nrl.com/draw/data?competition=111&season={SEASON}&round={round_name}"
    data = fetch_json(url)
    if not data:
        return []
    return data.get("fixtures", [])

def safe_int(v, default=0):
    try:
        return int(v)
    except Exception:
        return default

print("Downloading fixtures...")

fixtures = []
fixtures.extend(get_round("opening"))
fixtures.extend(get_round("all"))

print("Raw fixtures detected:", len(fixtures))

# dedupe fixtures
deduped = {}
for m in fixtures:
    mid = m.get("matchId") or m.get("id")
    home = m.get("homeTeam", {}).get("nickName", "")
    away = m.get("awayTeam", {}).get("nickName", "")
    key = str(mid) if mid else f"{home}|{away}|{m.get('roundTitle','')}|{m.get('clock',{}).get('kickOffTimeLong','')}"
    deduped[key] = m

fixtures = list(deduped.values())

print("Unique fixtures detected:", len(fixtures))

today = datetime.now(timezone.utc).date()
rows = []

for m in fixtures:
    match_id = m.get("matchId") or m.get("id")
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
        except Exception:
            round_num = 0
    else:
        round_num = 0

    kickoff = m.get("clock", {}).get("kickOffTimeLong", "")
    date_iso = kickoff[:10] if kickoff else ""

    # only include games up to today
    try:
        game_date = datetime.strptime(date_iso, "%Y-%m-%d").date()
        if game_date > today:
            continue
    except Exception:
        pass

    venue = m.get("venue", "")
    crowd = m.get("crowd") or m.get("attendance")

    home_points = safe_int(m.get("homeScore", 0), 0)
    away_points = safe_int(m.get("awayScore", 0), 0)

    # stable fallback match id
    if not match_id:
        match_id = f"{SEASON}R{round_num:02d}{home[:3]}{away[:3]}".upper()

    # try player stats endpoint
    player_rows = []
    stats_url = f"https://stats.nrl.com/api/match/{match_id}"
    stats = fetch_json(stats_url)

    if stats:
        for team in stats.get("teams", []):
            played_for = team.get("nickName", "")
            for p in team.get("players", []):
                tries = safe_int(p.get("tries", 0), 0)
                goals_made = safe_int(p.get("goals", p.get("goalsMade", 0)), 0)
                goals_attempted = safe_int(p.get("goalAttempts", p.get("goalsAttempted", 0)), 0)
                field_goals = safe_int(p.get("fieldGoals", p.get("field_goals", 0)), 0)
                points = safe_int(p.get("points", tries * 4 + goals_made * 2 + field_goals), 0)

                player_name = (
                    p.get("fullName")
                    or p.get("name")
                    or p.get("playerName")
                    or ""
                )

                if not player_name:
                    continue

                player_rows.append({
                    "season": SEASON,
                    "match_id": str(match_id),
                    "venue": venue,
                    "crowd": crowd,
                    "date_iso": date_iso,
                    "home_team": home,
                    "away_team": away,
                    "home_points": home_points,
                    "away_points": away_points,
                    "margin": abs(home_points - away_points),
                    "total_points": home_points + away_points,
                    "player": player_name,
                    "played_for": played_for,
                    "tries": tries,
                    "goals_made": goals_made,
                    "goals_attempted": goals_attempted,
                    "field_goals": field_goals,
                    "points": points
                })

    # if no player stats, still keep one fallback row so season page is not blank
    if player_rows:
        rows.extend(player_rows)
    else:
        rows.append({
            "season": SEASON,
            "match_id": str(match_id),
            "venue": venue,
            "crowd": crowd,
            "date_iso": date_iso,
            "home_team": home,
            "away_team": away,
            "home_points": home_points,
            "away_points": away_points,
            "margin": abs(home_points - away_points),
            "total_points": home_points + away_points,
            "player": "",
            "played_for": "",
            "tries": 0,
            "goals_made": 0,
            "goals_attempted": 0,
            "field_goals": 0,
            "points": 0
        })

# sort rows
rows.sort(key=lambda x: (x.get("date_iso", ""), x.get("match_id", ""), x.get("played_for", ""), x.get("player", "")))

print("Rows prepared:", len(rows))

# SAFETY: do not wipe the season file if nothing was found
if not rows:
    print("No rows found. Existing season file left untouched.")
    raise SystemExit(1)

with open(SEASON_FILE, "w", encoding="utf-8") as f:
    json.dump(rows, f, indent=2, ensure_ascii=False)

print("Season written:", SEASON_FILE)

# update index
if INDEX_FILE.exists():
    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            index = json.load(f)
    except Exception:
        index = {}
else:
    index = {}

if "seasons" not in index or not isinstance(index["seasons"], list):
    index["seasons"] = []

if SEASON not in index["seasons"]:
    index["seasons"].append(SEASON)

index["seasons"] = sorted(index["seasons"])

with open(INDEX_FILE, "w", encoding="utf-8") as f:
    json.dump(index, f, indent=2, ensure_ascii=False)

print("Index updated")
print("Update complete")
