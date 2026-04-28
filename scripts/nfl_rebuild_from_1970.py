#!/usr/bin/env python3
import os
import re
import json
import time
import random
from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Comment

START_YEAR = 1970
END_YEAR = datetime.now().year

BASE = "https://www.pro-football-reference.com"
OUT_ROOT = "docs/data/nfl"
SEASONS_DIR = os.path.join(OUT_ROOT, "seasons")
BOXSCORES_DIR = os.path.join(OUT_ROOT, "boxscores")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.3.1 Safari/605.1.15",
    "Accept-Language": "en-US,en;q=0.9",
}

def mkdirs():
    os.makedirs(SEASONS_DIR, exist_ok=True)
    os.makedirs(BOXSCORES_DIR, exist_ok=True)

def get(url):
    print(f"GET {url}")
    r = requests.get(url, headers=HEADERS, timeout=30)
    time.sleep(random.uniform(2.0, 4.5))
    if r.status_code != 200:
        print(f"  !! HTTP {r.status_code}")
        return None
    if "It looks like your ad blocker is on" in r.text:
        print("  !! blocked / adblock page returned")
        return None
    return r.text

def soup_with_comments(html):
    soup = BeautifulSoup(html, "html.parser")
    for c in soup.find_all(string=lambda text: isinstance(text, Comment)):
        if "<table" in c:
            extra = BeautifulSoup(c, "html.parser")
            soup.append(extra)
    return soup

def clean(s):
    return re.sub(r"\s+", " ", s or "").strip()

def table_rows(table):
    rows = []
    if not table:
        return rows
    for tr in table.select("tbody tr"):
        if "thead" in tr.get("class", []):
            continue
        row = {}
        for th in tr.find_all("th"):
            key = th.get("data-stat") or "row"
            row[key] = clean(th.get_text(" "))
        for td in tr.find_all("td"):
            key = td.get("data-stat")
            if key:
                row[key] = clean(td.get_text(" "))
        if row:
            rows.append(row)
    return rows

def parse_schedule(year):
    url = f"{BASE}/years/{year}/games.htm"
    html = get(url)
    if not html:
        return []

    soup = soup_with_comments(html)
    table = soup.find("table", id="games")
    games = []

    for tr in table.select("tbody tr") if table else []:
        if "thead" in tr.get("class", []):
            continue

        cells = {td.get("data-stat"): clean(td.get_text(" ")) for td in tr.find_all(["th", "td"])}
        box_td = tr.find("td", {"data-stat": "boxscore_word"})
        a = box_td.find("a") if box_td else None
        if not a:
            continue

        box_url = urljoin(BASE, a.get("href"))
        game_id = os.path.basename(box_url).replace(".htm", "")

        week = cells.get("week_num", "")
        date = cells.get("game_date", "")
        winner = cells.get("winner", "")
        loser = cells.get("loser", "")
        pts_win = cells.get("pts_win", "")
        pts_lose = cells.get("pts_lose", "")
        location = cells.get("game_location", "")
        boxscore_word = cells.get("boxscore_word", "")

        season_type = "regular"
        if "WildCard" in week or "Division" in week or "ConfChamp" in week or "SuperBowl" in week:
            season_type = "postseason"
        if boxscore_word.lower() == "preview":
            continue

        games.append({
            "season": year,
            "game_id": game_id,
            "week": week,
            "date": date,
            "season_type": season_type,
            "winner": winner,
            "loser": loser,
            "home_away_marker": location,
            "winner_points": to_int(pts_win),
            "loser_points": to_int(pts_lose),
            "boxscore_url": box_url,
            "boxscore_file": f"/data/nfl/boxscores/{year}/{game_id}.json"
        })

    return games

def to_int(v):
    try:
        return int(str(v).replace(",", "").strip())
    except:
        return None

def parse_scorebox(soup):
    title = clean(soup.find("h1").get_text(" ")) if soup.find("h1") else ""

    scorebox = soup.select_one(".scorebox")
    teams = []

    if scorebox:
        chunks = scorebox.find_all("div", recursive=False)
        for div in chunks[:2]:
            name_el = div.select_one("strong a") or div.select_one("strong")
            score_el = div.select_one(".score")
            if name_el:
                teams.append({
                    "team": clean(name_el.get_text(" ")),
                    "score": to_int(score_el.get_text(" ")) if score_el else None
                })

    meta = {}
    if scorebox:
        for div in scorebox.select(".scorebox_meta div"):
            txt = clean(div.get_text(" "))
            if "Start Time:" in txt:
                meta["start_time"] = txt.replace("Start Time:", "").strip()
            elif "Stadium:" in txt:
                meta["stadium"] = txt.replace("Stadium:", "").strip()
            elif "Attendance:" in txt:
                meta["attendance"] = txt.replace("Attendance:", "").strip()
            elif re.search(r"\w+day\s+\w+\s+\d{1,2},\s+\d{4}", txt):
                meta["date_full"] = txt

    return title, teams, meta

def parse_linescore(soup):
    table = soup.find("table", id="linescore")
    return table_rows(table)

def parse_game_info(soup):
    table = soup.find("table", id="game_info")
    data = {}
    for row in table_rows(table):
        key = row.get("row") or row.get("stat")
        val = row.get("stat") or row.get("value")
        if key and val and key != val:
            data[key] = val
    return data

def parse_boxscore(game):
    year = game["season"]
    game_id = game["game_id"]
    out_dir = os.path.join(BOXSCORES_DIR, str(year))
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, f"{game_id}.json")

    if os.path.exists(out_file):
        try:
            with open(out_file, "r", encoding="utf-8") as f:
                old = json.load(f)
            if old.get("game_id") == game_id and old.get("player_stats"):
                print(f"  skip existing complete {game_id}")
                return old
        except:
            pass

    html = get(game["boxscore_url"])
    if not html:
        return None

    soup = soup_with_comments(html)
    title, teams, meta = parse_scorebox(soup)

    player_tables = {
        "player_offense": "player_offense",
        "player_defense": "player_defense",
        "returns": "returns",
        "kicking": "kicking",
        "team_stats": "team_stats",
        "scoring": "scoring"
    }

    player_stats = {}
    for label, table_id in player_tables.items():
        player_stats[label] = table_rows(soup.find("table", id=table_id))

    data = {
        "season": year,
        "game_id": game_id,
        "source": game["boxscore_url"],
        "title": title,
        "week": game.get("week"),
        "date": game.get("date"),
        "season_type": game.get("season_type"),
        "teams": teams,
        "meta": meta,
        "summary": {
            "winner": game.get("winner"),
            "loser": game.get("loser"),
            "winner_points": game.get("winner_points"),
            "loser_points": game.get("loser_points"),
        },
        "linescore": parse_linescore(soup),
        "game_info": parse_game_info(soup),
        "player_stats": player_stats,
    }

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"  wrote {out_file}")
    return data

def write_season(year, games):
    out_file = os.path.join(SEASONS_DIR, f"{year}.json")
    data = {
        "season": year,
        "source": f"{BASE}/years/{year}/games.htm",
        "updated": datetime.utcnow().isoformat() + "Z",
        "games": games
    }
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"wrote {out_file} ({len(games)} games)")

def write_index():
    years = []
    for fn in sorted(os.listdir(SEASONS_DIR)):
        if fn.endswith(".json"):
            years.append(int(fn.replace(".json", "")))
    out = {
        "updated": datetime.utcnow().isoformat() + "Z",
        "years": years
    }
    with open(os.path.join(OUT_ROOT, "index.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

def main():
    mkdirs()

    total_games = 0
    total_boxes = 0

    for year in range(START_YEAR, END_YEAR + 1):
        print(f"\n===== NFL {year} =====")
        games = parse_schedule(year)

        good_games = []
        for g in games:
            box = parse_boxscore(g)
            if box:
                total_boxes += 1
                g["home_team"] = box["teams"][1]["team"] if len(box.get("teams", [])) > 1 else None
                g["away_team"] = box["teams"][0]["team"] if len(box.get("teams", [])) > 0 else None
                g["home_points"] = box["teams"][1]["score"] if len(box.get("teams", [])) > 1 else None
                g["away_points"] = box["teams"][0]["score"] if len(box.get("teams", [])) > 0 else None
                g["stadium"] = box.get("meta", {}).get("stadium")
                g["date_full"] = box.get("meta", {}).get("date_full")
            good_games.append(g)

        write_season(year, good_games)
        total_games += len(good_games)

    write_index()
    print("\nDONE")
    print(f"season games listed: {total_games}")
    print(f"boxscores written/read: {total_boxes}")

if __name__ == "__main__":
    main()
