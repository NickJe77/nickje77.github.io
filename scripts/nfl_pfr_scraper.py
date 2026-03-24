import json
import re
import time
import math
import random
import datetime as dt
from pathlib import Path
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import requests
from bs4 import BeautifulSoup, Comment

BASE = "https://www.pro-football-reference.com"
START_YEAR = 1970
END_YEAR = dt.date.today().year

OUT_DIR = Path("docs/data/nfl")
GAMES_DIR = OUT_DIR / "games"
BOX_DIR = OUT_DIR / "boxscores"
OUT_DIR.mkdir(parents=True, exist_ok=True)
GAMES_DIR.mkdir(parents=True, exist_ok=True)
BOX_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
                  "(KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.pro-football-reference.com/",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

MAX_WORKERS = 6
REQUEST_TIMEOUT = 30


def safe_int(v: Any) -> Optional[int]:
    try:
        if v is None:
            return None
        s = str(v).strip().replace(",", "")
        if s == "":
            return None
        if s.endswith(".0"):
            s = s[:-2]
        return int(float(s))
    except Exception:
        return None


def clean_text(v: Any) -> Any:
    if v is None:
        return None
    s = str(v)
    s = re.sub(r"\s+", " ", s).strip()
    return s if s != "" else None


def slug_from_href(href: str) -> str:
    return href.split("/")[-1].replace(".htm", "")


def fetch(url: str, retries: int = 5, sleep_base: float = 1.5) -> Optional[str]:
    for attempt in range(1, retries + 1):
        try:
            r = SESSION.get(url, timeout=REQUEST_TIMEOUT)
            if r.status_code == 200:
                return r.text
            if r.status_code in (404, 429, 500, 502, 503, 504):
                time.sleep(sleep_base * attempt + random.uniform(0.1, 0.8))
                continue
            return None
        except Exception:
            time.sleep(sleep_base * attempt + random.uniform(0.1, 0.8))
    return None


def table_nodes_from_html(html: str) -> List[BeautifulSoup]:
    soup = BeautifulSoup(html, "html.parser")
    nodes = list(soup.find_all("table"))

    for c in soup.find_all(string=lambda t: isinstance(t, Comment)):
        txt = str(c)
        if "<table" in txt:
            csoup = BeautifulSoup(txt, "html.parser")
            nodes.extend(csoup.find_all("table"))

    deduped = []
    seen = set()
    for t in nodes:
        tid = t.get("id") or str(t)[:120]
        if tid not in seen:
            deduped.append(t)
            seen.add(tid)
    return deduped


def parse_html_table(table_html: str) -> List[Dict[str, Any]]:
    try:
        dfs = pd.read_html(table_html)
        if not dfs:
            return []
        df = dfs[0]
        if isinstance(df.columns, pd.MultiIndex):
            cols = []
            for tup in df.columns:
                parts = [clean_text(x) for x in tup if clean_text(x)]
                cols.append(" | ".join(parts) if parts else "col")
            df.columns = cols
        else:
            df.columns = [clean_text(c) or "col" for c in df.columns]

        rows = []
        for row in df.to_dict(orient="records"):
            clean_row = {}
            for k, v in row.items():
                key = clean_text(k)
                if not key:
                    continue
                if pd.isna(v):
                    clean_row[key] = None
                else:
                    clean_row[key] = clean_text(v)
            if clean_row:
                rows.append(clean_row)
        return rows
    except Exception:
        return []


def extract_tables(html: str) -> Dict[str, List[Dict[str, Any]]]:
    out = {}
    for table in table_nodes_from_html(html):
        tid = table.get("id")
        if not tid:
            continue
        out[tid] = parse_html_table(str(table))
    return out


def extract_scorebox(soup: BeautifulSoup) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "teams": [],
        "scores": [],
        "records": [],
    }

    scorebox = soup.find("div", class_="scorebox")
    if not scorebox:
        return out

    team_tags = scorebox.select("div.scorebox strong a")
    for a in team_tags:
        name = clean_text(a.get_text(" ", strip=True))
        href = a.get("href")
        out["teams"].append({
            "name": name,
            "href": href,
            "team_id": href.strip("/").split("/")[-2] if href and "/teams/" in href else None
        })

    score_tags = scorebox.select("div.score")
    out["scores"] = [safe_int(x.get_text(" ", strip=True)) for x in score_tags]

    rec_tags = scorebox.select("div.scorebox div.scores > div")
    for div in rec_tags:
        txt = clean_text(div.get_text(" ", strip=True))
        if txt and re.match(r"^\(\d+-\d+.*\)$", txt):
            out["records"].append(txt)

    meta_lines = []
    meta = scorebox.find("div", class_="scorebox_meta")
    if meta:
        for d in meta.find_all("div"):
            txt = clean_text(d.get_text(" ", strip=True))
            if txt:
                meta_lines.append(txt)
    out["meta_lines"] = meta_lines
    return out


def extract_game_info_tables(tables: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    info = {}

    if "game_info" in tables:
        for row in tables["game_info"]:
            keys = list(row.keys())
            if len(keys) >= 2:
                k = clean_text(row.get(keys[0]))
                v = clean_text(row.get(keys[1]))
                if k:
                    info[k] = v

    if "officials" in tables:
        info["officials"] = tables["officials"]

    return info


def extract_scoring_summary(tables: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    for key in ("scoring", "scoring_drives", "scoring_summary"):
        if key in tables:
            return tables[key]
    return []


def extract_linescore(tables: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    for key in ("linescore", "vis_starters", "line_score"):
        if key in tables:
            return tables[key]
    return []


def extract_team_stats(tables: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    for key in ("team_stats", "game_stats"):
        if key in tables:
            return tables[key]
    return []


def parse_boxscore(url: str) -> Optional[Dict[str, Any]]:
    html = fetch(url)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    tables = extract_tables(html)

    game_id = slug_from_href(url)
    scorebox = extract_scorebox(soup)
    info = extract_game_info_tables(tables)

    title = None
    if soup.title:
        title = clean_text(soup.title.get_text(" ", strip=True))

    data: Dict[str, Any] = {
        "game_id": game_id,
        "url": url,
        "title": title,
        "scorebox": scorebox,
        "game_info": info,
        "linescore": extract_linescore(tables),
        "team_stats": extract_team_stats(tables),
        "scoring_summary": extract_scoring_summary(tables),
        "tables": tables,
    }

    if scorebox.get("meta_lines"):
        # usually first meta line contains the game date/time
        data["game_date_display"] = scorebox["meta_lines"][0]

    return data


def parse_schedule_year(year: int) -> List[Dict[str, Any]]:
    url = f"{BASE}/years/{year}/games.htm"
    print(f"Discovering {year} schedule: {url}")
    html = fetch(url)
    if not html:
        print(f"  Skipped {year} (no schedule page)")
        return []

    soup = BeautifulSoup(html, "html.parser")
    rows = []

    games_table = soup.find("table", id="games")
    if not games_table:
        comments = soup.find_all(string=lambda t: isinstance(t, Comment))
        for c in comments:
            if 'id="games"' in str(c):
                csoup = BeautifulSoup(str(c), "html.parser")
                games_table = csoup.find("table", id="games")
                if games_table:
                    break

    if not games_table:
        print(f"  No games table found for {year}")
        return []

    tbody = games_table.find("tbody")
    if not tbody:
        return []

    for tr in tbody.find_all("tr"):
        if "class" in tr.attrs and "thead" in tr.get("class", []):
            continue

        date_cell = tr.find("th", {"data-stat": "game_date"})
        if not date_cell:
            continue

        row: Dict[str, Any] = {"season": year}

        def cell(stat: str) -> Optional[str]:
            td = tr.find(attrs={"data-stat": stat})
            return clean_text(td.get_text(" ", strip=True)) if td else None

        date_text = clean_text(date_cell.get_text(" ", strip=True))
        row["date"] = date_text
        row["week"] = cell("week_num")
        row["day"] = cell("game_day_of_week")
        row["time"] = cell("gametime")
        row["winner"] = cell("winner")
        row["loser"] = cell("loser")
        row["winner_points"] = safe_int(cell("pts_win"))
        row["loser_points"] = safe_int(cell("pts_lose"))
        row["yards_winner"] = safe_int(cell("yards_win"))
        row["turnovers_winner"] = safe_int(cell("to_win"))
        row["yards_loser"] = safe_int(cell("yards_lose"))
        row["turnovers_loser"] = safe_int(cell("to_lose"))
        row["location_note"] = cell("game_location")
        row["ot"] = cell("overtime")
        row["attendance"] = safe_int(cell("attendance"))
        row["stadium"] = cell("stadium")

        box_td = tr.find(attrs={"data-stat": "boxscore_word"})
        box_a = box_td.find("a") if box_td else None
        href = box_a.get("href") if box_a else None
        if href and href.startswith("/boxscores/"):
            row["boxscore_path"] = href
            row["boxscore_url"] = BASE + href
            row["game_id"] = slug_from_href(href)
            rows.append(row)

    print(f"  Found {len(rows)} games for {year}")
    return rows


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_existing_box(game_id: str, year: int) -> Optional[Dict[str, Any]]:
    path = BOX_DIR / str(year) / f"{game_id}.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def save_box(year: int, game_id: str, data: Dict[str, Any]) -> None:
    path = BOX_DIR / str(year) / f"{game_id}.json"
    save_json(path, data)


def scrape_year(year: int) -> List[Dict[str, Any]]:
    schedule_games = parse_schedule_year(year)
    if not schedule_games:
        return []

    season_games: List[Dict[str, Any]] = []

    futures = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        for game in schedule_games:
            game_id = game["game_id"]
            existing = load_existing_box(game_id, year)
            if existing:
                merged = dict(game)
                merged["boxscore"] = existing
                season_games.append(merged)
            else:
                fut = ex.submit(parse_boxscore, game["boxscore_url"])
                futures[fut] = game

        completed = 0
        total = len(futures)
        for fut in as_completed(futures):
            game = futures[fut]
            completed += 1
            game_id = game["game_id"]

            try:
                box = fut.result()
            except Exception:
                box = None

            merged = dict(game)
            merged["boxscore"] = box
            season_games.append(merged)

            if box:
                save_box(year, game_id, box)

            if completed % 25 == 0 or completed == total:
                print(f"  {year}: {completed}/{total} new boxscores done")

    season_games.sort(key=lambda x: (x.get("date") or "", x.get("game_id") or ""))
    return season_games


def build_index(all_years: List[Dict[str, Any]]) -> Dict[str, Any]:
    seasons = []
    total_games = 0
    latest_game_date = None

    for y in all_years:
        year = y["season"]
        game_count = len(y["games"])
        total_games += game_count

        dates = [g.get("date") for g in y["games"] if g.get("date")]
        if dates:
            mx = max(dates)
            if not latest_game_date or mx > latest_game_date:
                latest_game_date = mx

        seasons.append({
            "season": year,
            "games": game_count,
            "file": f"/data/nfl/games/{year}.json"
        })

    return {
        "sport": "NFL",
        "start_season": START_YEAR,
        "end_season": END_YEAR,
        "updated_at_utc": dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "total_games": total_games,
        "latest_game_date": latest_game_date,
        "seasons": seasons
    }


def main():
    print(f"Scraping NFL {START_YEAR} to {END_YEAR}")

    all_years = []

    for year in range(START_YEAR, END_YEAR + 1):
        try:
            games = scrape_year(year)
            if not games:
                continue

            year_payload = {
                "season": year,
                "updated_at_utc": dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
                "games": games
            }
            save_json(GAMES_DIR / f"{year}.json", year_payload)

            all_years.append({
                "season": year,
                "games": games
            })

            print(f"Saved {year}: {len(games)} games")
        except Exception as e:
            print(f"FAILED YEAR {year}: {e}")

    index = build_index(all_years)
    save_json(OUT_DIR / "index.json", index)

    print("DONE")


if __name__ == "__main__":
    main()
