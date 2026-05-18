import os
import re
import json
import time
import argparse
from datetime import datetime
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

START_SEASON = 1976
CURRENT_SEASON = datetime.now().year if datetime.now().month >= 8 else datetime.now().year - 1

OUT_BASE = "docs/data/basketball"
SEASONS_DIR = os.path.join(OUT_BASE, "seasons")
BOXSCORES_DIR = os.path.join(OUT_BASE, "boxscores")

BBR = "https://www.basketball-reference.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/"
}

session = requests.Session()

TEAM_MAP = {
    "ATL":"Atlanta Hawks",
    "BOS":"Boston Celtics",
    "BRK":"Brooklyn Nets",
    "CHI":"Chicago Bulls",
    "CLE":"Cleveland Cavaliers",
    "DAL":"Dallas Mavericks",
    "DEN":"Denver Nuggets",
    "DET":"Detroit Pistons",
    "GSW":"Golden State Warriors",
    "HOU":"Houston Rockets",
    "IND":"Indiana Pacers",
    "LAC":"Los Angeles Clippers",
    "LAL":"Los Angeles Lakers",
    "MEM":"Memphis Grizzlies",
    "MIA":"Miami Heat",
    "MIL":"Milwaukee Bucks",
    "MIN":"Minnesota Timberwolves",
    "NOP":"New Orleans Pelicans",
    "NYK":"New York Knicks",
    "OKC":"Oklahoma City Thunder",
    "ORL":"Orlando Magic",
    "PHI":"Philadelphia 76ers",
    "PHO":"Phoenix Suns",
    "POR":"Portland Trail Blazers",
    "SAC":"Sacramento Kings",
    "SAS":"San Antonio Spurs",
    "TOR":"Toronto Raptors",
    "UTA":"Utah Jazz",
    "WAS":"Washington Wizards",
}

def ensure_dirs():

    os.makedirs(SEASONS_DIR, exist_ok=True)
    os.makedirs(BOXSCORES_DIR, exist_ok=True)

def clean(text):

    return re.sub(r"\s+", " ", str(text or "")).strip()

def safe_int(v):

    try:
        return int(float(str(v).replace(",", "")))
    except:
        return 0

def save_json(path, data):

    os.makedirs(os.path.dirname(path), exist_ok=True)

    temp = path + ".tmp"

    with open(temp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    os.replace(temp, path)

def load_json(path):

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None

def get(url, sleep=2.5):

    time.sleep(sleep)

    retries = 5

    for attempt in range(retries):

        try:

            r = session.get(
                url,
                headers=HEADERS,
                timeout=60
            )

            if r.status_code == 200:
                return r.text

            if r.status_code == 403:

                wait = 10 * (attempt + 1)

                print(f"403 BLOCKED {url}")
                print(f"WAITING {wait}s")

                time.sleep(wait)

                continue

            print(f"BAD STATUS {r.status_code} {url}")

            return None

        except Exception as e:

            print(f"REQUEST FAILED {e}")

            time.sleep(5)

    return None

def parse_schedule_table(html, season_start, game_type):

    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table", id="schedule")

    if not table:
        return []

    games = []

    for row in table.select("tbody tr"):

        if "thead" in row.get("class", []):
            continue

        box = row.find("td", {"data-stat":"box_score_text"})

        if not box:
            continue

        a = box.find("a")

        if not a:
            continue

        href = a.get("href", "")

        if not href:
            continue

        game_id = os.path.splitext(
            os.path.basename(href)
        )[0]

        away_team = clean(
            row.find("td", {"data-stat":"visitor_team_name"}).get_text(" ", strip=True)
        )

        home_team = clean(
            row.find("td", {"data-stat":"home_team_name"}).get_text(" ", strip=True)
        )

        away_score = safe_int(
            row.find("td", {"data-stat":"visitor_pts"}).get_text(" ", strip=True)
        )

        home_score = safe_int(
            row.find("td", {"data-stat":"home_pts"}).get_text(" ", strip=True)
        )

        date = clean(
            row.find(["td","th"], {"data-stat":"date_game"}).get_text(" ", strip=True)
        )

        games.append({
            "game_id": game_id,
            "date": date,
            "season": season_start,
            "type": game_type,
            "home_team": home_team,
            "away_team": away_team,
            "home_score": home_score,
            "away_score": away_score,
            "winner": home_team if home_score > away_score else away_team,
            "score": f"{away_score} - {home_score}",
            "boxscore_url": urljoin(BBR, href),
            "game_file": f"{game_id}.json"
        })

    return games

def get_regular_games(season_start):

    year = season_start + 1

    url = f"{BBR}/leagues/NBA_{year}_games.html"

    html = get(url)

    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")

    urls = [url]

    filt = soup.find("div", class_="filter")

    if filt:

        for a in filt.find_all("a", href=True):

            u = urljoin(BBR, a["href"])

            if u not in urls:
                urls.append(u)

    all_games = []

    for u in urls:

        page = html if u == url else get(u)

        if not page:
            continue

        all_games.extend(
            parse_schedule_table(
                page,
                season_start,
                "Regular Season"
            )
        )

    return all_games

def get_playoff_games(season_start):

    year = season_start + 1

    url = f"{BBR}/playoffs/NBA_{year}_games.html"

    html = get(url)

    if not html:
        return []

    return parse_schedule_table(
        html,
        season_start,
        "Playoffs"
    )

def parse_boxscore(game):

    html = get(game["boxscore_url"], sleep=2.5)

    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")

    players = []
    team_totals = []
    inactive_players = []

    all_tables = soup.find_all("table")

    for table in all_tables:

        tid = table.get("id", "")

        if not tid.endswith("_basic"):
            continue

        tbody = table.find("tbody")

        if not tbody:
            continue

        team_code = tid.replace("_basic", "").upper()

        team_name = TEAM_MAP.get(
            team_code,
            team_code
        )

        for row in tbody.find_all("tr"):

            if "thead" in row.get("class", []):
                continue

            player_cell = row.find(
                "th",
                {"data-stat":"player"}
            )

            if not player_cell:
                continue

            player_name = clean(
                player_cell.get_text(" ", strip=True)
            )

            if player_name == "":
                continue

            if player_name.lower() == "team totals":

                totals = {
                    "team": team_name
                }

                for td in row.find_all("td"):

                    stat = td.get("data-stat", "")

                    val = clean(
                        td.get_text(" ", strip=True)
                    )

                    totals[stat] = val

                team_totals.append(totals)

                continue

            if player_name.lower() == "reserves":
                continue

            mp = row.find("td", {"data-stat":"mp"})

            inactive = False

            if mp:

                mp_text = clean(
                    mp.get_text(" ", strip=True)
                )

                if mp_text == "":
                    inactive = True

            player_url = ""

            a = player_cell.find("a")

            if a and a.get("href"):

                player_url = urljoin(
                    BBR,
                    a["href"]
                )

            pdata = {
                "player": player_name,
                "team": team_name,
                "player_url": player_url,
                "inactive": inactive
            }

            for td in row.find_all("td"):

                stat = td.get("data-stat", "")

                val = clean(
                    td.get_text(" ", strip=True)
                )

                pdata[stat] = val

            players.append(pdata)

            if inactive:
                inactive_players.append(player_name)

    attendance = 0

    try:

        text = soup.get_text("\n", strip=True)

        m = re.search(
            r"Attendance:\s*([\d,]+)",
            text
        )

        if m:
            attendance = safe_int(m.group(1))

    except:
        pass

    arena = ""

    try:

        text = soup.get_text("\n", strip=True)

        m = re.search(
            r"Arena:\s*(.*?)\n",
            text
        )

        if m:
            arena = clean(m.group(1))

    except:
        pass

    officials = []

    try:

        text = soup.get_text("\n", strip=True)

        m = re.search(
            r"Officials:\s*(.*?)\n",
            text,
            re.I
        )

        if m:

            officials = [
                clean(x)
                for x in m.group(1).split(",")
                if clean(x)
            ]

    except:
        pass

    return {
        **game,
        "playoff": game["type"] == "Playoffs",
        "arena": arena,
        "attendance": attendance,
        "officials": officials,
        "inactive_players": inactive_players,
        "team_totals": team_totals,
        "players": players
    }

def process_game(game, out_file, overwrite=False):

    existing = load_json(out_file)

    if existing and not overwrite:
        return existing

    box = parse_boxscore(game)

    if not box:
        return None

    save_json(out_file, box)

    return box

def build_season(season_start, overwrite=False):

    print("=" * 80)
    print(f"BUILDING SEASON {season_start}")
    print("=" * 80)

    regular = get_regular_games(season_start)

    playoffs = get_playoff_games(season_start)

    games = regular + playoffs

    deduped = {}

    for g in games:
        deduped[g["game_id"]] = g

    games = list(deduped.values())

    games.sort(key=lambda x: x["date"])

    if len(games) == 0:

        print(f"NO GAMES FOUND FOR {season_start}")

        return

    season_box_dir = os.path.join(
        BOXSCORES_DIR,
        str(season_start)
    )

    os.makedirs(season_box_dir, exist_ok=True)

    index = []

    futures = []

    MAX_WORKERS = 3

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:

        for game in games:

            out_file = os.path.join(
                season_box_dir,
                game["game_file"]
            )

            futures.append(
                executor.submit(
                    process_game,
                    game,
                    out_file,
                    overwrite
                )
            )

        completed = 0

        for future in as_completed(futures):

            completed += 1

            try:

                box = future.result()

                if not box:
                    continue

                index.append({
                    "game_id": box["game_id"],
                    "date": box["date"],
                    "season": season_start,
                    "type": box["type"],
                    "home_team": box["home_team"],
                    "away_team": box["away_team"],
                    "home_score": box["home_score"],
                    "away_score": box["away_score"],
                    "winner": box["winner"],
                    "score": box["score"],
                    "playoff": box["playoff"],
                    "arena": box.get("arena", ""),
                    "attendance": box.get("attendance", 0),
                    "game_file": box["game_file"]
                })

                if completed % 25 == 0:
                    print(f"{season_start}: {completed}/{len(games)} completed")

            except Exception as e:

                print(f"THREAD FAILED {e}")

    index.sort(key=lambda x: x["date"])

    season_file = os.path.join(
        SEASONS_DIR,
        f"{season_start}.json"
    )

    save_json(season_file, index)

    print(f"SAVED {season_file} WITH {len(index)} GAMES")

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--start",
        type=int,
        default=START_SEASON
    )

    parser.add_argument(
        "--end",
        type=int,
        default=CURRENT_SEASON
    )

    parser.add_argument(
        "--overwrite",
        action="store_true"
    )

    args = parser.parse_args()

    ensure_dirs()

    for season in range(
        args.start,
        args.end + 1
    ):

        build_season(
            season,
            overwrite=args.overwrite
        )

    print("COMPLETE")

if __name__ == "__main__":
    main()
