import json
from pathlib import Path
from urllib.request import Request, urlopen

FILE = Path("docs/data/nrl/matches/2026.json")
BASE = "https://site.api.espn.com/apis/site/v2/sports/rugby-league/3/scoreboard"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def fetch_json(url: str):
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

if not FILE.exists():
    raise FileNotFoundError(f"Missing file: {FILE}")

with open(FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

existing = {str(row.get("match_id", "")) for row in data}

base = fetch_json(BASE)
calendar = base.get("leagues", [{}])[0].get("calendar", [])

added = 0

for iso_date in calendar:
    yyyymmdd = iso_date[:10].replace("-", "")
    day = fetch_json(f"{BASE}?dates={yyyymmdd}")

    for event in day.get("events", []):
        match_id = str(event.get("id", ""))

        if not match_id or match_id in existing:
            continue

        comp = (event.get("competitions") or [{}])[0]
        status = (((comp.get("status") or {}).get("type") or {}))
        if not status.get("completed", False):
            continue

        competitors = comp.get("competitors") or []
        home = next((c for c in competitors if c.get("homeAway") == "home"), {})
        away = next((c for c in competitors if c.get("homeAway") == "away"), {})

        home_team = ((home.get("team") or {}).get("displayName")) or ((home.get("team") or {}).get("name")) or ""
        away_team = ((away.get("team") or {}).get("displayName")) or ((away.get("team") or {}).get("name")) or ""

        home_points = int(home.get("score") or 0)
        away_points = int(away.get("score") or 0)

        venue = (comp.get("venue") or {}).get("fullName", "")
        attendance = comp.get("attendance")

        row = {
            "season": 2026,
            "match_id": match_id,
            "venue": venue,
            "crowd": attendance,
            "date_iso": (event.get("date") or "")[:10],
            "home_team": home_team,
            "away_team": away_team,
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
        }

        data.append(row)
        existing.add(match_id)
        added += 1

with open(FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print(f"Added matches: {added}")
