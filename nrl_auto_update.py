import json
import re
from io import StringIO
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd

FILE = Path("docs/data/nrl/matches/2026.json")
SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/rugby-league/3/scoreboard"
PLAYERSTATS_URL = "https://www.espn.com.au/nrl/playerstats/_/gameId/{game_id}/league/3"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def fetch_json(url: str):
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

def fetch_text(url: str):
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="ignore")

def clean_player_name(value: str) -> str:
    s = str(value).strip()
    s = re.sub(r"^\d+\s+", "", s)
    s = re.sub(r",\s*[A-Z/]+$", "", s)
    s = s.replace("  ", " ").strip()
    return s

def get_stat_col(df, names):
    cols = {str(c).strip().lower(): c for c in df.columns}
    for name in names:
        if name.lower() in cols:
            return cols[name.lower()]
    return None

def extract_team_tables(html: str):
    tables = pd.read_html(StringIO(html))
    out = []

    for df in tables:
        if df.empty:
            continue

        first_col = str(df.columns[0]).strip().lower()

        if "name" not in first_col:
            continue

        work = df.copy()
        work.columns = [str(c).strip() for c in work.columns]

        name_col = work.columns[0]
        work[name_col] = work[name_col].astype(str)

        # keep actual player rows only
        work = work[~work[name_col].str.contains("Replacements", case=False, na=False)]
        work = work[work[name_col].str.match(r"^\d+\s+", na=False)]

        if work.empty:
            continue

        tries_col = get_stat_col(work, ["T", "Tries"])
        goals_col = get_stat_col(work, ["G", "Goals"])
        dg_col = get_stat_col(work, ["DG", "Drop Goals", "FG", "Field Goals"])
        points_col = get_stat_col(work, ["PTS", "Points"])

        team_rows = []
        for _, row in work.iterrows():
            player = clean_player_name(row[name_col])
            if not player:
                continue

            def as_int(col):
                if not col:
                    return 0
                val = row.get(col, 0)
                if pd.isna(val):
                    return 0
                s = str(val).strip()
                s = re.sub(r"[^\d-]", "", s)
                return int(s) if s not in ("", "-", None) else 0

            team_rows.append({
                "player": player,
                "tries": as_int(tries_col),
                "goals_made": as_int(goals_col),
                "goals_attempted": as_int(goals_col),
                "field_goals": as_int(dg_col),
                "points": as_int(points_col),
            })

        if len(team_rows) >= 10:
            out.append(team_rows)

    return out[:2]

if not FILE.exists():
    raise FileNotFoundError(f"Missing file: {FILE}")

with open(FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

existing = {str(r.get("match_id", "")) for r in data if str(r.get("player", "")).strip()}

base = fetch_json(SCOREBOARD)
calendar = base.get("leagues", [{}])[0].get("calendar", [])

added_matches = 0
added_rows = 0

for iso_date in calendar:
    yyyymmdd = iso_date[:10].replace("-", "")
    day = fetch_json(f"{SCOREBOARD}?dates={yyyymmdd}")

    for event in day.get("events", []):
        match_id = str(event.get("id", ""))

        if not match_id or match_id in existing:
            continue

        comp = (event.get("competitions") or [{}])[0]
        status = ((comp.get("status") or {}).get("type") or {})
        if not status.get("completed", False):
            continue

        competitors = comp.get("competitors") or []
        home = next((c for c in competitors if c.get("homeAway") == "home"), {})
        away = next((c for c in competitors if c.get("homeAway") == "away"), {})

        home_team = ((home.get("team") or {}).get("displayName")) or ""
        away_team = ((away.get("team") or {}).get("displayName")) or ""
        home_points = int(home.get("score") or 0)
        away_points = int(away.get("score") or 0)
        venue = (comp.get("venue") or {}).get("fullName", "")
        attendance = comp.get("attendance")

        html = fetch_text(PLAYERSTATS_URL.format(game_id=match_id))
        team_tables = extract_team_tables(html)

        if len(team_tables) < 2:
            continue

        home_rows, away_rows = team_tables[0], team_tables[1]

        for played_for, rows in ((home_team, home_rows), (away_team, away_rows)):
            for p in rows:
                data.append({
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
                    "player": p["player"],
                    "played_for": played_for,
                    "tries": p["tries"],
                    "goals_made": p["goals_made"],
                    "goals_attempted": p["goals_attempted"],
                    "field_goals": p["field_goals"],
                    "points": p["points"],
                })
                added_rows += 1

        existing.add(match_id)
        added_matches += 1

with open(FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print(f"Added matches: {added_matches}")
print(f"Added rows: {added_rows}")
