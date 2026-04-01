import requests
import json
import time
from pathlib import Path
from datetime import datetime, timezone

print("MLB 2026 SAFE REBUILD")

BASE = "https://statsapi.mlb.com/api/v1"
HEADERS = {"User-Agent": "Mozilla/5.0"}

SEASON = 2026
START_DATE = "2026-03-26"
TODAY_UTC = datetime.now(timezone.utc).strftime("%Y-%m-%d")

OUT_DIR = Path(f"docs/data/baseball/boxscores/{SEASON}")
OUT_DIR.mkdir(parents=True, exist_ok=True)

TEAM_MAP = {
    108: "LAA", 109: "ARI", 110: "BAL", 111: "BOS", 112: "CHC",
    113: "CIN", 114: "CLE", 115: "COL", 116: "DET", 117: "HOU",
    118: "KC", 119: "LAD", 120: "WSH", 121: "NYM", 133: "OAK",
    134: "PIT", 135: "SD", 136: "SEA", 137: "SF", 138: "STL",
    139: "TB", 140: "TEX", 141: "TOR", 142: "MIN", 143: "PHI",
    144: "ATL", 145: "CWS", 146: "MIA", 147: "NYY", 158: "MIL",
}

PLAYER_ID_CACHE = Path("docs/data/baseball/players.json")


def safe_get(url, timeout=30):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def load_existing_player_map():
    mapping = {}
    if PLAYER_ID_CACHE.exists():
        try:
            with open(PLAYER_ID_CACHE, "r", encoding="utf-8") as f:
                rows = json.load(f)
            for row in rows:
                pid = str(row.get("player_id", "")).strip()
                sid = str(row.get("short_id", "")).strip()
                name = str(row.get("name", "")).strip()
                if pid:
                    mapping[pid] = {
                        "short_id": sid if sid else pid,
                        "name": name
                    }
        except Exception:
            pass
    return mapping


def save_player_map(mapping):
    rows = []
    for pid, info in sorted(mapping.items(), key=lambda x: x[0]):
        rows.append({
            "player_id": pid,
            "short_id": info.get("short_id", pid),
            "name": info.get("name", "")
        })
    with open(PLAYER_ID_CACHE, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)


def make_short_id(full_name, used_short_ids):
    name = (full_name or "").strip()
    if not name:
        return ""

    parts = [p for p in name.replace(".", "").replace("'", "").replace("-", " ").split() if p]
    if len(parts) == 1:
        first = parts[0]
        last = parts[0]
    else:
        first = parts[0]
        last = parts[-1]

    base = (last[:5].lower() + first[:3].lower()).ljust(8, "x")[:8]

    for i in range(1, 1000):
        sid = f"{base}{i:03d}"
        if sid not in used_short_ids:
            used_short_ids.add(sid)
            return sid

    return base + "999"


def get_schedule_games():
    url = f"{BASE}/schedule?sportId=1&season={SEASON}&gameType=R,P"
    data = safe_get(url)
    if not data:
        return []

    games = []
    for d in data.get("dates", []):
        for g in d.get("games", []):

            game_date = str(g.get("gameDate", ""))[:10]
            if not game_date:
                continue

            if game_date < START_DATE or game_date > TODAY_UTC:
                continue

            status = g.get("status", {}).get("codedGameState", "")
            if status not in {"F", "O", "I"}:
                continue

            home_id = g.get("teams", {}).get("home", {}).get("team", {}).get("id")
            away_id = g.get("teams", {}).get("away", {}).get("team", {}).get("id")

            games.append({
                "gamePk": g.get("gamePk"),
                "date": game_date,
                "home": TEAM_MAP.get(home_id, "UNK"),
                "away": TEAM_MAP.get(away_id, "UNK"),
            })

    return games


def build_header(game):
    game_id = f"{game['home']}{game['date'].replace('-', '')}0"
    date_slash = game["date"].replace("-", "/")
    return [
        ["id", game_id],
        ["version", "2"],
        ["info", "visteam", game["away"]],
        ["info", "hometeam", game["home"]],
        ["info", "date", date_slash],
    ]


def get_start_rows(game_pk, player_map, used_short_ids):
    url = f"{BASE}/game/{game_pk}/feed/live"
    data = safe_get(url)
    if not data:
        return []

    teams = data.get("liveData", {}).get("boxscore", {}).get("teams", {})
    rows = []

    for side_name, bat_flag in [("away", "0"), ("home", "1")]:
        side = teams.get(side_name, {})
        players = side.get("players", {})
        batting_order = side.get("battingOrder", []) or []

        slot = 1
        for pid_raw in batting_order:
            pid = str(pid_raw).replace("ID", "").strip()
            p = players.get(f"ID{pid}", {}) or players.get(pid, {}) or {}

            person = p.get("person", {}) or {}
            full_name = person.get("fullName", "") or ""

            if pid and pid not in player_map:
                player_map[pid] = {
                    "short_id": make_short_id(full_name, used_short_ids) if full_name else pid,
                    "name": full_name
                }

            short_id = player_map.get(pid, {}).get("short_id", pid if pid else "")
            position = str((p.get("position", {}) or {}).get("code", "10"))
            batting_slot = str(slot)

            if short_id:
                rows.append(["start", short_id, full_name, side.get("team", {}).get("abbreviation", ""), batting_slot, position])

            slot += 1

    return rows


def get_play_events(game_pk, player_map, used_short_ids):
    url = f"{BASE}/game/{game_pk}/playByPlay"
    data = safe_get(url)
    if not data:
        return []

    plays = data.get("allPlays", [])
    events = []

    for p in plays:
        try:
            inning = str(p.get("about", {}).get("inning", ""))
            half = p.get("about", {}).get("halfInning", "")
            bat_flag = "0" if half == "top" else "1"

            batter = p.get("matchup", {}).get("batter", {}) or {}
            pid = str(batter.get("id", "")).strip()
            full_name = batter.get("fullName", "") or ""

            if pid and pid not in player_map:
                player_map[pid] = {
                    "short_id": make_short_id(full_name, used_short_ids) if full_name else pid,
                    "name": full_name
                }

            short_id = player_map.get(pid, {}).get("short_id", pid if pid else "")

            if inning and short_id:
                events.append(["play", inning, bat_flag, short_id, "0", "UNK", ""])

        except Exception:
            continue

    return events


def build_one_game(game, player_map, used_short_ids):
    fname = f"{game['date']}_{game['away']}_{game['home']}.json"
    out_file = OUT_DIR / fname

    if out_file.exists():
        return "exists"

    full = safe_get(f"{BASE}/game/{game['gamePk']}/feed/live")
    if not full:
        return "no_data"

    teams = full.get("liveData", {}).get("boxscore", {}).get("teams", {})

    batting = []
    pitching = []

    for side in ["away", "home"]:
        players = teams.get(side, {}).get("players", {})

        for p in players.values():
            name = p.get("person", {}).get("fullName", "")
            stats = p.get("stats", {})

            b = stats.get("batting")
            if b:
                batting.append({
                    "team": side,
                    "name": name,
                    "AB": b.get("atBats", 0),
                    "R": b.get("runs", 0),
                    "H": b.get("hits", 0),
                    "RBI": b.get("rbi", 0),
                    "BB": b.get("baseOnBalls", 0),
                    "SO": b.get("strikeOuts", 0)
                })

            pit = stats.get("pitching")
            if pit:
                pitching.append({
                    "team": side,
                    "name": name,
                    "IP": pit.get("inningsPitched", "0.0"),
                    "H": pit.get("hits", 0),
                    "R": pit.get("runs", 0),
                    "ER": pit.get("earnedRuns", 0),
                    "BB": pit.get("baseOnBalls", 0),
                    "SO": pit.get("strikeOuts", 0)
                })

    header = build_header(game)
    starts = get_start_rows(game["gamePk"], player_map, used_short_ids)
    plays = get_play_events(game["gamePk"], player_map, used_short_ids)

    if not plays:
        return "no_plays"

    data = {
        "game_id": f"{game['home']}{game['date'].replace('-', '')}0",
        "date": game["date"],
        "season": SEASON,
        "home_code": game["home"],
        "away_code": game["away"],
        "home_team": game["home"],
        "away_team": game["away"],
        "batting": batting,
        "pitching": pitching,
        "events": header + starts + plays
    }

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return "built"


def main():
    games = get_schedule_games()
    print(f"Found {len(games)} eligible 2026 games")

    player_map = load_existing_player_map()
    used_short_ids = {
        info.get("short_id", "")
        for info in player_map.values()
        if info.get("short_id", "")
    }

    built = 0
    exists = 0
    no_plays = 0

    for game in games:
        result = build_one_game(game, player_map, used_short_ids)

        if result == "built":
            built += 1
            print(f"Built: {game['date']}_{game['away']}_{game['home']}.json")
        elif result == "exists":
            exists += 1
        elif result == "no_plays":
            no_plays += 1
            print(f"No plays yet: {game['date']}_{game['away']}_{game['home']}")

        time.sleep(0.2)

    save_player_map(player_map)

    print("")
    print(f"Built files: {built}")
    print(f"Already existed: {exists}")
    print(f"No plays yet: {no_plays}")


if __name__ == "__main__":
    main()
