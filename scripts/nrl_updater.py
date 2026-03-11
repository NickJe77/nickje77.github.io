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


print("Discovering matches")

# ---------------------------------------------------
# Match-centre index endpoint (contains real match IDs)
# ---------------------------------------------------

index_url = f"https://www.nrl.com/match-centre/data?season={SEASON}"

data = fetch_json(index_url)

if not data:
    print("Failed to load match index")
    raise SystemExit()

matches = data.get("matches", [])

print("Matches discovered:", len(matches))


# -----------------------------
# Load existing matches
# -----------------------------

existing = []

if MATCH_FILE.exists():
    with open(MATCH_FILE) as f:
        existing = json.load(f)

existing_ids = {m["match_id"] for m in existing}

print("Existing matches:", len(existing_ids))


def fetch_stats(match_id):

    url = f"https://www.nrl.com/match-centre/{match_id}/statistics"

    return fetch_json(url)


rows = existing.copy()

added = 0

for m in matches:

    match_id = str(m.get("matchId"))

    if not match_id:
        continue

    if match_id in existing_ids:
        continue

    stats = fetch_stats(match_id)

    if not stats:
        continue

    players = []

    for t in stats.get("teams", []):

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

    row = {
        "season": SEASON,
        "match_id": match_id,
        "venue": m.get("venue"),
        "date_iso": m.get("date", "")[:10],
        "home_team": m.get("homeTeam", {}).get("nickName"),
        "away_team": m.get("awayTeam", {}).get("nickName"),
        "home_points": m.get("homeScore", 0),
        "away_points": m.get("awayScore", 0),
        "margin": abs(m.get("homeScore", 0) - m.get("awayScore", 0)),
        "total_points": m.get("homeScore", 0) + m.get("awayScore", 0),
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
