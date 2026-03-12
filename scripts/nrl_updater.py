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


def fetch(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None


print("Discovering matches")

index_url = f"https://www.nrl.com/match-centre/data/competitions/111/seasons/{SEASON}/matches"

data = fetch(index_url)

if not data:
    print("Failed to load match index")
    raise SystemExit()


matches = data.get("matches", [])

print("Matches detected:", len(matches))


match_ids = [str(m.get("matchId")) for m in matches if m.get("matchId")]

match_ids = sorted(list(set(match_ids)))

print("Unique matches:", len(match_ids))


existing = []

if MATCH_FILE.exists():
    try:
        with open(MATCH_FILE) as f:
            content = f.read().strip()
            if content:
                existing = json.loads(content)
    except:
        existing = []

existing_ids = {m["match_id"] for m in existing}

print("Existing matches:", len(existing_ids))


rows = existing.copy()
added = 0


def get_stats(match_id):

    url = f"https://www.nrl.com/match-centre/{match_id}/statistics"

    return fetch(url)


for match_id in match_ids:

    if match_id in existing_ids:
        continue

    stats = get_stats(match_id)

    if not stats:
        continue

    players = []

    for team in stats.get("teams", []):

        team_name = team.get("teamNickName")

        for p in team.get("players", []):

            players.append({
                "player": p.get("displayName"),
                "played_for": team_name,
                "tries": p.get("tries", 0),
                "goals_made": p.get("goals", 0),
                "goals_attempted": p.get("goalAttempts", 0),
                "field_goals": p.get("fieldGoals", 0),
                "points": p.get("points", 0),
                "runs": p.get("runs", 0),
                "metres": p.get("runMetres", 0),
                "tackles": p.get("tacklesMade", 0),
                "missed_tackles": p.get("missedTackles", 0),
                "offloads": p.get("offloads", 0)
            })

    if not players:
        continue

    rows.append({
        "season": SEASON,
        "match_id": match_id,
        "players": players
    })

    added += 1

    print("Added match", match_id)


if rows:

    with open(MATCH_FILE, "w") as f:
        json.dump(rows, f, indent=2)

print("Matches added:", added)
print("Updater complete")
