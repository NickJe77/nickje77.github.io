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


def get_fixtures():

    fixtures = []

    for r in range(0, 30):

        round_name = "opening" if r == 0 else f"round-{r}"

        url = f"https://www.nrl.com/draw/data?competition=111&season={SEASON}&round={round_name}"

        data = fetch(url)

        if not data:
            continue

        fixtures.extend(data.get("fixtures", []))

    return fixtures


print("Discovering fixtures")

fixtures = get_fixtures()

print("Fixtures detected:", len(fixtures))


match_ids = []

for f in fixtures:

    match = f.get("match")

    if match and match.get("matchId"):

        match_ids.append(str(match.get("matchId")))


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

        team_name = tea_
