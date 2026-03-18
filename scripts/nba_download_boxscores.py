import requests
import json
import os
import unicodedata
import re
from datetime import datetime, timezone

BASE_DIR = "docs/data/nba"
SEASON = "2025"

print("Downloading NBA boxscores for season", SEASON)

today = datetime.now(timezone.utc)

season_path = os.path.join(BASE_DIR, SEASON)
index_path = os.path.join(season_path, "index.json")

with open(index_path) as f:
    index = json.load(f)

games_saved = 0
games_skipped = 0


# ---------- MINUTES ----------
def convert_minutes(raw):

    if not raw:
        return "0:00"

    if isinstance(raw, str) and raw.startswith("PT"):
        try:
            m = raw.replace("PT", "").replace("S", "").split("M")
            mins = int(m[0])
            secs = int(float(m[1]))
            return f"{mins}:{secs:02d}"
        except:
            return "0:00"

    return str(raw)


# ---------- 🔥 NAME NORMALIZATION (CRITICAL FIX) ----------
def normalize_name(name):
    if not name:
        return ""

    # remove accents (Dončić -> Doncic)
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ascii", "ignore").decode("ascii")

    # remove punctuation
    name = re.sub(r"[^\w\s]", "", name)

    # clean spaces
    name = re.sub(r"\s+", " ", name).strip()

    return name


# ---------- CLEAN NAME ----------
def clean_name(p):

    first = p.get("firstName", "")
    last = p.get("familyName", "")

    if first or last:
        return normalize_name(f"{first} {last}".strip())

    if p.get("name"):
        return normalize_name(p["name"])

    if p.get("nameI"):
        # 🔥 IGNORE INITIAL FORMAT IF FULL NAME EXISTS
        full = normalize_name(p.get("name", ""))
        if full:
            return full
        return normalize_name(p["nameI"])

    return "Unknown"


# ---------- MAIN LOOP ----------
for game_id in index["games"]:

    # skip preseason
    if game_id.startswith("001"):
        continue

    box_url = f"https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{game_id}.json"

    try:
        r = requests.get(box_url, timeout=30)
    except:
        games_skipped += 1
        continue

    if r.status_code != 200:
        games_skipped += 1
        continue

    game = r.json()["game"]

    game_time = game.get("gameTimeUTC")

    # skip future games
    if game_time:
        try:
            dt = datetime.fromisoformat(game_time.replace("Z", "+00:00"))
            if dt > today:
                continue
        except:
            pass

    home = game["homeTeam"]
    away = game["awayTeam"]

    home_team = f'{home.get("teamCity","")} {home.get("teamName","")}'.strip()
    away_team = f'{away.get("teamCity","")} {away.get("teamName","")}'.strip()

    output = {
        "game_id": game_id,
        "date": game_time,
        "game_type": "Regular Season",
        "home_team": home_team,
        "away_team": away_team,
        "home_score": home.get("score", 0),
        "away_score": away.get("score", 0),
        "arena": game.get("arena", {}).get("arenaName", ""),
        "players": []
    }

    for team_key in ["homeTeam", "awayTeam"]:

        team = game.get(team_key, {})
        team_name = f'{team.get("teamCity","")} {team.get("teamName","")}'.strip()

        for p in team.get("players", []):

            stats = p.get("statistics", {})

            player_name = clean_name(p)

            # 🔥 FINAL SAFETY (NEVER allow accents through)
            player_name = normalize_name(player_name)

            output["players"].append({
                "player": player_name,
                "team": team_name,
                "minutes": convert_minutes(stats.get("minutes")),
                "points": stats.get("points", 0),
                "rebounds": stats.get("reboundsTotal", 0),
                "assists": stats.get("assists", 0),
                "steals": stats.get("steals", 0),
                "blocks": stats.get("blocks", 0),
                "turnovers": stats.get("turnovers", 0)
            })

    game_file = os.path.join(season_path, f"{game_id}.json")

    with open(game_file, "w") as f:
        json.dump(output, f, indent=2)

    games_saved += 1
    print("Saved", game_file)


print("Games saved:", games_saved)
print("Games skipped:", games_skipped)
