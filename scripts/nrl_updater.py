import json
import requests
from pathlib import Path

print("NRL FULL UPDATER")

SEASON = 2026

BASE = Path("docs/data/nrl")
MATCH_FILE = BASE / "matches" / f"{SEASON}.json"

BASE.mkdir(parents=True, exist_ok=True)
MATCH_FILE.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}


def fetch_json(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None


def get_round(round_name):

    url = f"https://www.nrl.com/draw/data?competition=111&season={SEASON}&round={round_name}"

    data = fetch_json(url)

    if not data:
        return []

    return data.get("fixtures", [])


print("Discovering fixtures")

fixtures = []

fixtures.extend(get_round("opening"))

for r in range(1, 30):
    fixtures.extend(get_round(f"round-{r}"))

print("Fixtures detected:", len(fixtures))


# -----------------------------
# Extract match IDs correctly
# -----------------------------

dedup = {}

for m in fixtures:

    mid = None

    # possible locations
    if "matchId" in m:
        mid = m["matchId"]

    elif "match" in m and isinstance(m["match"], dict):
        mid = m["match"].get("matchId")

    elif "id" in m:
        mid = m["id"]

    if mid:
        dedup[str(mid)] = m


fixtures = list(dedup.values())

print("Unique matches:", len(fixtures))


# -----------------------------
# Load existing matches
# -----------------------------

existing = []

if MATCH_FILE.exists():
    with open(MATCH_FILE) as f:
        existing = json.load(f)

existing_ids = {m["match_id"] for m in existing}

print("Existing matches:", len(existing_ids))


# -----------------------------
# Fetch match statistics
# -----------------------------

def fetch_stats(match_id):

    url = f"https://www.nrl.com/match-centre/{match_id}/statistics"

    return fetch_json(url)


rows = existing.copy()

added = 0

for m in fixtures:

    match_id = None

    if "matchId" in m:
        match_id = str(m["matchId"])

    elif "match" in m and isinstance(m["match"], dict):
        match_id = str(m["match"].get("matchId"))

    elif "id" in m:
        match_id = str(m["id"])

    if not match_id:
        continue

    if match_id in existing_ids:
        continue

    stats = fetch_stats(match_id)

    if not stats:
        continue

    players = []

    teams = stats.get("teams", [])

    for t in teams:

        team_name = t.get("teamNickName")

        for p in t.get("players", []):

            players.append({
                "player": p.get("displayName"),
                "played_for": team_name,
                "tries": p.get("tries", 0),
                "goals_made": p.get("goals", 0),
                "goals_attempted": p.get("goalAttempts", 0),
                "field_goals": p.get("fieldGoals", 0),
                "points": p.get("points", 0)
            })

    if not players:
        continue

    kickoff = m.get("clock", {}).get("kickOffTimeLong", "")

    home_score = m.get("homeScore", 0)
    away_score = m.get("awayScore", 0)

    row = {
        "season": SEASON,
        "match_id": match_id,
        "venue": m.get("venue"),
        "date_iso": kickoff[:10],
        "home_team": m.get("homeTeam", {}).get("nickName"),
        "away_team": m.get("awayTeam", {}).get("nickName"),
        "home_points": home_score,
        "away_points": away_score,
        "margin": abs(home_score - away_score),
        "total_points": home_score + away_score,
        "players": players
    }

    rows.append(row)

    added += 1

    print("Added match", match_id, "players:", len(players))


if added == 0:

    print("No new matches found")

else:

    rows.sort(key=lambda x: x["date_iso"])

    with open(MATCH_FILE, "w") as f:
        json.dump(rows, f, indent=2)

    print("Matches added:", added)

print("Updater complete")
