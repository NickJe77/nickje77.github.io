import os
import json
import re
from collections import defaultdict

BASE = "docs/data/baseball"
BOX_DIR = os.path.join(BASE, "boxscores")
PLAYERS_DIR = os.path.join(BASE, "players")
PLAYERS_INDEX = os.path.join(BASE, "players.json")

os.makedirs(PLAYERS_DIR, exist_ok=True)

TEAM_NAMES = {
    "ARI": "Arizona Diamondbacks",
    "ATL": "Atlanta Braves",
    "BAL": "Baltimore Orioles",
    "BOS": "Boston Red Sox",
    "CHC": "Chicago Cubs",
    "CHN": "Chicago Cubs",
    "CHW": "Chicago White Sox",
    "CIN": "Cincinnati Reds",
    "CLE": "Cleveland Guardians",
    "COL": "Colorado Rockies",
    "DET": "Detroit Tigers",
    "HOU": "Houston Astros",
    "KC": "Kansas City Royals",
    "KAN": "Kansas City Royals",
    "LAA": "Los Angeles Angels",
    "LAD": "Los Angeles Dodgers",
    "LAN": "Los Angeles Dodgers",
    "LOS": "Los Angeles Dodgers",
    "MIA": "Miami Marlins",
    "MIL": "Milwaukee Brewers",
    "MIN": "Minnesota Twins",
    "NYM": "New York Mets",
    "NYY": "New York Yankees",
    "ATH": "Athletics",
    "OAK": "Athletics",
    "PHI": "Philadelphia Phillies",
    "PIT": "Pittsburgh Pirates",
    "SD": "San Diego Padres",
    "SDP": "San Diego Padres",
    "SEA": "Seattle Mariners",
    "SF": "San Francisco Giants",
    "SFG": "San Francisco Giants",
    "STL": "St Louis Cardinals",
    "TB": "Tampa Bay Rays",
    "TBR": "Tampa Bay Rays",
    "TEX": "Texas Rangers",
    "TOR": "Toronto Blue Jays",
    "WSH": "Washington Nationals",
    "WSN": "Washington Nationals",
}

def slugify(name):
    name = str(name or "").lower()
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"\s+", "-", name.strip())
    return name

def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def team_name(code):
    if isinstance(code, dict):
        return code.get("name") or TEAM_NAMES.get(code.get("code"), code.get("code", ""))
    return TEAM_NAMES.get(str(code), str(code or ""))

def empty_line():
    return {
        "AB": 0,
        "R": 0,
        "H": 0,
        "RBI": 0,
        "HR": 0,
        "BB": 0,
        "SO": 0
    }

def add_line(target, source):
    for k in ["AB", "R", "H", "RBI", "HR", "BB", "SO"]:
        target[k] += int(source.get(k, 0) or 0)

def get_player_name_from_index(code, player_index):
    if not code:
        return ""
    code = str(code)

    if code in player_index:
        v = player_index[code]
        if isinstance(v, str):
            return v
        if isinstance(v, dict):
            return v.get("name") or v.get("full_name") or v.get("player") or code

    return code

def load_player_index():
    data = load_json(PLAYERS_INDEX)
    out = {}

    if isinstance(data, dict):
        for k, v in data.items():
            out[str(k)] = v

    elif isinstance(data, list):
        for row in data:
            if not isinstance(row, dict):
                continue

            code = (
                row.get("id")
                or row.get("code")
                or row.get("player_id")
                or row.get("retro_id")
                or row.get("key")
            )

            name = (
                row.get("name")
                or row.get("full_name")
                or row.get("player")
            )

            if code and name:
                out[str(code)] = name

    return out

def parse_retrosheet_event(event_code):
    s = str(event_code or "").upper()
    line = empty_line()

    if not s:
        return line

    if s.startswith("W") or s.startswith("IW"):
        line["BB"] = 1
        return line

    if s.startswith("K"):
        line["AB"] = 1
        line["SO"] = 1
        return line

    if s.startswith("S"):
        line["AB"] = 1
        line["H"] = 1
        return line

    if s.startswith("D"):
        line["AB"] = 1
        line["H"] = 1
        return line

    if s.startswith("T"):
        line["AB"] = 1
        line["H"] = 1
        return line

    if s.startswith("HR") or s.startswith("H"):
        line["AB"] = 1
        line["H"] = 1
        line["HR"] = 1
        line["R"] = 1
        return line

    if s.startswith("E"):
        line["AB"] = 1
        return line

    if s.startswith("FC"):
        line["AB"] = 1
        return line

    if re.match(r"^[0-9]", s):
        line["AB"] = 1
        return line

    return line

def parse_retrosheet_boxscore(game, player_index):
    rows = []

    date = game.get("date", "")
    season = game.get("season", "")
    home_code = game.get("home_code") or game.get("home_team")
    away_code = game.get("away_code") or game.get("away_team")

    events = game.get("events", [])

    game_lines = {}

    for ev in events:
        if not isinstance(ev, list):
            continue

        if len(ev) < 7:
            continue

        if ev[0] != "play":
            continue

        inning = ev[1]
        batting_side = ev[2]
        batter_code = ev[3]
        event_code = ev[6]

        if not batter_code:
            continue

        if str(batting_side) == "0":
            team = away_code
            opponent = home_code
        else:
            team = home_code
            opponent = away_code

        player_name = get_player_name_from_index(batter_code, player_index)

        key = (player_name, date, season, team, opponent)

        if key not in game_lines:
            game_lines[key] = {
                "name": player_name,
                "date": date,
                "season": season,
                "team": team_name(team),
                "opponent": team_name(opponent),
                **empty_line()
            }

        line = parse_retrosheet_event(event_code)
        add_line(game_lines[key], line)

    rows.extend(game_lines.values())
    return rows

def extract_stat_from_mlb_player(p):
    batting = (
        p.get("stats", {})
         .get("batting", {})
    )

    if not batting:
        return None

    return {
        "AB": int(batting.get("atBats", 0) or 0),
        "R": int(batting.get("runs", 0) or 0),
        "H": int(batting.get("hits", 0) or 0),
        "RBI": int(batting.get("rbi", 0) or 0),
        "HR": int(batting.get("homeRuns", 0) or 0),
        "BB": int(batting.get("baseOnBalls", 0) or 0),
        "SO": int(batting.get("strikeOuts", 0) or 0),
    }

def parse_mlb_api_boxscore(game):
    rows = []

    date = game.get("date", "")
    season = game.get("season", "")

    home = game.get("home_team") or {}
    away = game.get("away_team") or {}

    home_name = team_name(home)
    away_name = team_name(away)

    boxscore = (
        game.get("liveData", {})
            .get("boxscore", {})
            .get("teams", {})
    )

    for side, team_obj, opponent_obj in [
        ("home", home, away),
        ("away", away, home)
    ]:
        players = (
            boxscore
            .get(side, {})
            .get("players", {})
        )

        for _, p in players.items():
            if not isinstance(p, dict):
                continue

            person = p.get("person", {})
            name = person.get("fullName") or person.get("boxscoreName")

            if not name:
                continue

            stat = extract_stat_from_mlb_player(p)

            if not stat:
                continue

            if stat["AB"] == 0 and stat["BB"] == 0 and stat["R"] == 0 and stat["H"] == 0 and stat["RBI"] == 0:
                continue

            rows.append({
                "name": name,
                "date": date,
                "season": season,
                "team": team_name(team_obj),
                "opponent": team_name(opponent_obj),
                **stat
            })

    return rows

def parse_game(path, player_index):
    game = load_json(path)

    if not isinstance(game, dict):
        return []

    if "events" in game:
        return parse_retrosheet_boxscore(game, player_index)

    if "liveData" in game:
        return parse_mlb_api_boxscore(game)

    return []

def main():
    player_index = load_player_index()

    all_players = defaultdict(lambda: {
        "name": "",
        "games": []
    })

    total_files = 0
    total_rows = 0

    for season in sorted(os.listdir(BOX_DIR)):
        season_dir = os.path.join(BOX_DIR, season)

        if not os.path.isdir(season_dir):
            continue

        for filename in sorted(os.listdir(season_dir)):
            if not filename.endswith(".json"):
                continue

            path = os.path.join(season_dir, filename)
            rows = parse_game(path, player_index)

            total_files += 1
            total_rows += len(rows)

            for row in rows:
                name = row.pop("name", "").strip()

                if not name:
                    continue

                slug = slugify(name)

                if not slug:
                    continue

                all_players[slug]["name"] = name
                all_players[slug]["games"].append(row)

    index = []

    for slug, pdata in sorted(all_players.items()):
        pdata["games"].sort(
            key=lambda g: str(g.get("date", "")),
            reverse=True
        )

        out_path = os.path.join(PLAYERS_DIR, f"{slug}.json")
        save_json(out_path, pdata)

        index.append({
            "name": pdata["name"],
            "slug": slug,
            "games": len(pdata["games"])
        })

    save_json(os.path.join(PLAYERS_DIR, "index.json"), index)

    print("DONE")
    print(f"Boxscore files read: {total_files}")
    print(f"Player game rows built: {total_rows}")
    print(f"Player files written: {len(all_players)}")
    print(f"Index written: {os.path.join(PLAYERS_DIR, 'index.json')}")

if __name__ == "__main__":
    main()
