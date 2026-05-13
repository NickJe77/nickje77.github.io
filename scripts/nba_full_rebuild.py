import os
import re
import json
import time
import argparse
from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Comment

START_SEASON = 1976
CURRENT_SEASON = datetime.now().year if datetime.now().month >= 8 else datetime.now().year - 1

OUT_BASE = "docs/data/basketball"
SEASONS_DIR = os.path.join(OUT_BASE, "seasons")
BOXSCORES_DIR = os.path.join(OUT_BASE, "boxscores")

BBR = "https://www.basketball-reference.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
}

TEAM_MAP = {
    "ATL": "Atlanta Hawks", "BOS": "Boston Celtics", "BRK": "Brooklyn Nets",
    "NJN": "New Jersey Nets", "CHO": "Charlotte Hornets", "CHH": "Charlotte Hornets",
    "CHA": "Charlotte Bobcats", "CHI": "Chicago Bulls", "CLE": "Cleveland Cavaliers",
    "DAL": "Dallas Mavericks", "DEN": "Denver Nuggets", "DET": "Detroit Pistons",
    "GSW": "Golden State Warriors", "HOU": "Houston Rockets", "IND": "Indiana Pacers",
    "LAC": "Los Angeles Clippers", "SDC": "San Diego Clippers", "BUF": "Buffalo Braves",
    "LAL": "Los Angeles Lakers", "MEM": "Memphis Grizzlies", "VAN": "Vancouver Grizzlies",
    "MIA": "Miami Heat", "MIL": "Milwaukee Bucks", "MIN": "Minnesota Timberwolves",
    "NOH": "New Orleans Hornets", "NOK": "New Orleans/Oklahoma City Hornets",
    "NOP": "New Orleans Pelicans", "NYK": "New York Knicks", "OKC": "Oklahoma City Thunder",
    "SEA": "Seattle SuperSonics", "ORL": "Orlando Magic", "PHI": "Philadelphia 76ers",
    "PHO": "Phoenix Suns", "POR": "Portland Trail Blazers", "SAC": "Sacramento Kings",
    "KCK": "Kansas City Kings", "KCO": "Kansas City-Omaha Kings", "CIN": "Cincinnati Royals",
    "SAS": "San Antonio Spurs", "TOR": "Toronto Raptors", "UTA": "Utah Jazz",
    "NOJ": "New Orleans Jazz", "WAS": "Washington Wizards", "WSB": "Washington Bullets",
}

def ensure_dirs():
    os.makedirs(SEASONS_DIR, exist_ok=True)
    os.makedirs(BOXSCORES_DIR, exist_ok=True)

def get(url, sleep=4):
    print(f"GET {url}")
    time.sleep(sleep)
    r = requests.get(url, headers=HEADERS, timeout=45)
    if r.status_code != 200:
        print(f"BAD STATUS {r.status_code}: {url}")
        return None
    return r.text

def soup_from_html(html):
    return BeautifulSoup(html, "html.parser")

def clean(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()

def safe_int(v):
    try:
        if v in ("", None):
            return 0
        return int(float(str(v).replace(",", "")))
    except Exception:
        return 0

def table_from_soup_or_comments(soup, table_id):
    table = soup.find("table", id=table_id)
    if table:
        return table

    for c in soup.find_all(string=lambda t: isinstance(t, Comment)):
        if table_id in c:
            csoup = BeautifulSoup(c, "html.parser")
            table = csoup.find("table", id=table_id)
            if table:
                return table

    return None

def parse_schedule_table(html, season_start, game_type):
    soup = soup_from_html(html)
    table = soup.find("table", id="schedule")
    if not table:
        return []

    games = []

    for row in table.select("tbody tr"):
        if "thead" in row.get("class", []):
            continue

        box = row.find("td", {"data-stat": "box_score_text"})
        if not box or not box.find("a"):
            continue

        href = box.find("a").get("href", "")
        if not href:
            continue

        boxscore_url = urljoin(BBR, href)
        game_id = os.path.splitext(os.path.basename(href))[0]

        date = clean(row.find(["th", "td"], {"data-stat": "date_game"}).get_text(" ", strip=True)) if row.find(["th", "td"], {"data-stat": "date_game"}) else ""

        away_team = clean(row.find("td", {"data-stat": "visitor_team_name"}).get_text(" ", strip=True)) if row.find("td", {"data-stat": "visitor_team_name"}) else ""
        home_team = clean(row.find("td", {"data-stat": "home_team_name"}).get_text(" ", strip=True)) if row.find("td", {"data-stat": "home_team_name"}) else ""

        away_score = safe_int(row.find("td", {"data-stat": "visitor_pts"}).get_text(" ", strip=True)) if row.find("td", {"data-stat": "visitor_pts"}) else 0
        home_score = safe_int(row.find("td", {"data-stat": "home_pts"}).get_text(" ", strip=True)) if row.find("td", {"data-stat": "home_pts"}) else 0

        venue = clean(row.find("td", {"data-stat": "arena_name"}).get_text(" ", strip=True)) if row.find("td", {"data-stat": "arena_name"}) else ""
        attendance = safe_int(row.find("td", {"data-stat": "attendance"}).get_text(" ", strip=True)) if row.find("td", {"data-stat": "attendance"}) else 0

        winner = home_team if home_score > away_score else away_team if away_score > home_score else ""

        games.append({
            "game_id": game_id,
            "date": date,
            "season": season_start,
            "type": game_type,
            "game_type": game_type,
            "home_team": home_team,
            "away_team": away_team,
            "home_score": home_score,
            "away_score": away_score,
            "winner": winner,
            "score": f"{away_score} – {home_score}",
            "venue": venue,
            "attendance": attendance,
            "boxscore_url": boxscore_url,
            "game_file": f"{game_id}.json"
        })

    return games

def get_regular_games(season_start):
    bbr_year = season_start + 1
    first_url = f"{BBR}/leagues/NBA_{bbr_year}_games.html"
    html = get(first_url)
    if not html:
        return []

    soup = soup_from_html(html)

    urls = [first_url]

    filt = soup.find("div", class_="filter")
    if filt:
        for a in filt.find_all("a", href=True):
            u = urljoin(BBR, a["href"])
            if f"NBA_{bbr_year}_games" in u and u not in urls:
                urls.append(u)

    all_games = []

    for url in urls:
        page = html if url == first_url else get(url)
        if not page:
            continue
        all_games.extend(parse_schedule_table(page, season_start, "Regular Season"))

    return all_games

def get_playoff_games(season_start):
    bbr_year = season_start + 1
    url = f"{BBR}/playoffs/NBA_{bbr_year}_games.html"
    html = get(url)

    if html:
        games = parse_schedule_table(html, season_start, "Playoffs")
        if games:
            return games

    fallback = f"{BBR}/playoffs/NBA_{bbr_year}.html"
    html = get(fallback)
    if not html:
        return []

    soup = soup_from_html(html)

    games = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/boxscores/" not in href or not href.endswith(".html"):
            continue

        boxscore_url = urljoin(BBR, href)
        game_id = os.path.splitext(os.path.basename(href))[0]

        if game_id in seen:
            continue
        seen.add(game_id)

        games.append({
            "game_id": game_id,
            "date": "",
            "season": season_start,
            "type": "Playoffs",
            "game_type": "Playoffs",
            "home_team": "",
            "away_team": "",
            "home_score": 0,
            "away_score": 0,
            "winner": "",
            "score": "",
            "venue": "",
            "attendance": 0,
            "boxscore_url": boxscore_url,
            "game_file": f"{game_id}.json"
        })

    return games

def parse_line_score(soup):
    table = soup.find("table", id="line_score")
    if not table:
        return {}

    teams = []

    for tr in table.select("tbody tr"):
        th = tr.find("th")
        if not th:
            continue

        team_code = clean(th.get_text(" ", strip=True))
        pts_cell = tr.find("td", {"data-stat": "pts"})
        pts = safe_int(pts_cell.get_text(" ", strip=True)) if pts_cell else 0

        teams.append({
            "team_code": team_code,
            "team": TEAM_MAP.get(team_code, team_code),
            "score": pts
        })

    if len(teams) >= 2:
        return {
            "away_team": teams[0]["team"],
            "home_team": teams[1]["team"],
            "away_score": teams[0]["score"],
            "home_score": teams[1]["score"]
        }

    return {}

def parse_meta(soup):
    meta = {
        "date": "",
        "venue": "",
        "attendance": 0
    }

    scorebox = soup.find("div", class_="scorebox_meta")
    if not scorebox:
        return meta

    parts = [clean(x.get_text(" ", strip=True)) for x in scorebox.find_all("div")]

    for p in parts:
        if re.search(r"\b\d{4}\b", p) and not meta["date"]:
            meta["date"] = p

        if "Arena:" in p:
            meta["venue"] = clean(p.replace("Arena:", ""))

        if "Attendance:" in p:
            meta["attendance"] = safe_int(p.replace("Attendance:", ""))

    return meta

def parse_basic_table(soup, team_code):
    table_id = f"box-{team_code}-game-basic"
    table = table_from_soup_or_comments(soup, table_id)
    if not table:
        return []

    players = []

    for tr in table.select("tbody tr"):
        if "thead" in tr.get("class", []):
            continue

        th = tr.find("th", {"data-stat": "player"})
        if not th:
            continue

        name = clean(th.get_text(" ", strip=True))
        if not name or name.lower() == "reserves":
            continue

        row = {
            "player": name,
            "team_code": team_code,
            "team": TEAM_MAP.get(team_code, team_code),
        }

        for td in tr.find_all("td"):
            stat = td.get("data-stat")
            if not stat:
                continue
            row[stat] = clean(td.get_text(" ", strip=True))

        players.append(row)

    return players

def parse_boxscore(game):
    html = get(game["boxscore_url"], sleep=5)
    if not html:
        return None

    soup = soup_from_html(html)

    line = parse_line_score(soup)
    meta = parse_meta(soup)

    box = dict(game)

    for k, v in line.items():
        if v not in ("", 0, None):
            box[k] = v

    for k, v in meta.items():
        if v not in ("", 0, None):
            box[k] = v

    winner = box["home_team"] if box["home_score"] > box["away_score"] else box["away_team"] if box["away_score"] > box["home_score"] else ""

    box["winner"] = winner
    box["score"] = f'{box["away_score"]} – {box["home_score"]}'
    box["playoff"] = box["type"] == "Playoffs"

    team_codes = []
    for table in soup.find_all("table"):
        tid = table.get("id", "")
        m = re.match(r"box-([A-Z0-9]{3})-game-basic", tid)
        if m:
            team_codes.append(m.group(1))

    team_codes = list(dict.fromkeys(team_codes))

    players = []
    for code in team_codes:
        players.extend(parse_basic_table(soup, code))

    box["players"] = players

    return box

def load_existing(path):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None

def save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def build_season(season_start, overwrite=False):
    print("\n" + "=" * 80)
    print(f"BUILDING BASKETBALL / NBA SEASON {season_start}")
    print("=" * 80)

    regular = get_regular_games(season_start)
    playoffs = get_playoff_games(season_start)

    games = regular + playoffs

    deduped = {}
    for g in games:
        deduped[g["game_id"]] = g

    games = list(deduped.values())
    games.sort(key=lambda x: x.get("date", ""))

    season_box_dir = os.path.join(BOXSCORES_DIR, str(season_start))
    os.makedirs(season_box_dir, exist_ok=True)

    index = []

    for i, game in enumerate(games, start=1):
        out_file = os.path.join(season_box_dir, game["game_file"])

        existing = load_existing(out_file)

        if existing and not overwrite:
            box = existing
            print(f"[{season_start}] {i}/{len(games)} EXISTS {game['game_id']}")
        else:
            print(f"[{season_start}] {i}/{len(games)} SCRAPE {game['game_id']} {game['type']}")
            box = parse_boxscore(game)

            if not box:
                print(f"FAILED BOXSCORE {game['game_id']}")
                continue

            save(out_file, box)

        index.append({
            "game_id": box.get("game_id", game["game_id"]),
            "date": box.get("date", game.get("date", "")),
            "season": season_start,
            "type": box.get("type", game.get("type", "")),
            "game_type": box.get("game_type", game.get("game_type", "")),
            "home_team": box.get("home_team", game.get("home_team", "")),
            "away_team": box.get("away_team", game.get("away_team", "")),
            "home_score": safe_int(box.get("home_score", game.get("home_score", 0))),
            "away_score": safe_int(box.get("away_score", game.get("away_score", 0))),
            "winner": box.get("winner", game.get("winner", "")),
            "score": box.get("score", game.get("score", "")),
            "venue": box.get("venue", game.get("venue", "")),
            "attendance": safe_int(box.get("attendance", game.get("attendance", 0))),
            "playoff": box.get("playoff", game.get("type") == "Playoffs"),
            "game_file": game["game_file"]
        })

    season_file = os.path.join(SEASONS_DIR, f"{season_start}.json")
    save(season_file, index)

    print(f"SAVED {season_file} WITH {len(index)} GAMES")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=START_SEASON)
    parser.add_argument("--end", type=int, default=CURRENT_SEASON)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    ensure_dirs()

    for season in range(args.start, args.end + 1):
        build_season(season, overwrite=args.overwrite)

    print("\nCOMPLETE")

if __name__ == "__main__":
    main()
