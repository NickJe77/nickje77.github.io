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
# Extract match IDs properly
# -----------------------------

dedup = {}

for m in fixtures:

    mid = (
        m.get("matchId")
        or m.get("match_id")
        or m.get("fixtureId")
        or m.get("id")
    )

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

    return fetc
