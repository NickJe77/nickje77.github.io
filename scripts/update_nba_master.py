#!/usr/bin/env python3
"""
Update NBA per-game JSON files in-repo (append-only) using NBA live JSON.

Writes new game files to:
  docs/data/nba/<season_folder>/<int(gameId)>.json

Example:
  NBA gameId "0012500001" -> filename "12500001.json"
"""

from __future__ import annotations

import json
import os
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests


# ----------------------------
# Config (env overrides)
# ----------------------------
BASE_DIR = Path("docs/data/nba")
SESSION_FOLDER = os.getenv("NBA_SEASON_FOLDER", "2025").strip()  # you confirmed still "2025"
OUT_DIR = BASE_DIR / SESSION_FOLDER

# How many DAYS to process per run (prevents timeouts during big catch-up)
MAX_DAYS_PER_RUN = int(os.getenv("NBA_MAX_DAYS_PER_RUN", "7"))

# How many NEW games to write per run (extra safety)
MAX_GAMES_PER_RUN = int(os.getenv("NBA_MAX_GAMES_PER_RUN", "60"))

# Continue from a cursor (so you can catch up from Feb to now safely)
CURSOR_PATH = BASE_DIR / "_nba_update_cursor.json"

# Include preseason/play-in/playoffs? (default: regular season + playoffs + play-in; exclude preseason)
INCLUDE_PRESEASON = os.getenv("NBA_INCLUDE_PRESEASON", "0").strip() in ("1", "true", "yes", "y")

# Backfill window each run to catch missed games (in addition to cursor)
BACKFILL_DAYS = int(os.getenv("NBA_BACKFILL_DAYS", "2"))

# NBA endpoints
SCOREBOARD_URL = "https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_{yyyymmdd}.json"
BOXSCORE_URL = "https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{gameId}.json"

# HTTP
TIMEOUT = 30
RETRIES = 3
SLEEP_BETWEEN_CALLS_SEC = 0.35


# ----------------------------
# Helpers
# ----------------------------
def http_get_json(url: str) -> Dict[str, Any]:
    last_err = None
    for i in range(RETRIES):
        try:
            r = requests.get(url, timeout=TIMEOUT, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last_err = e
            time.sleep(1.0 + i * 1.5)
    raise RuntimeError(f"Failed GET after {RETRIES} tries: {url}\nLast error: {last_err}")


def yyyymmdd(d: date) -> str:
    return d.strftime("%Y%m%d")


def safe_int_filename(game_id_str: str) -> str:
    # NBA gameId has leading zeros; your repo uses int() string (e.g. "0012500001" -> "12500001")
    return str(int(game_id_str))


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def parse_date_iso(s: str) -> Optional[date]:
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


def find_latest_existing_game_date(season_dir: Path) -> Optional[date]:
    if not season_dir.exists():
        return None

    latest: Optional[date] = None
    # Avoid scanning tens of thousands of files fully: sample by reading last modified order is not reliable on GH.
    # We'll scan filenames but only parse a bounded number of newest-looking IDs if directory is huge.
    # However your season folder for current year should be manageable.
    candidates = [p for p in season_dir.glob("*.json") if p.is_file()]
    if not candidates:
        return None

    # Sort by numeric game_id filename, descending, and parse the top N files for dates.
    # This is fast and usually correct because newer games have higher ids within same season code.
    candidates.sort(key=lambda p: int(p.stem) if p.stem.isdigit() else -1, reverse=True)

    for p in candidates[:500]:  # cap parsing work
        try:
            d = load_json(p)
            di = parse_date_iso(str(d.get("date", "")).strip())
            if di and (latest is None or di > latest):
                latest = di
        except Exception:
            continue

    # If nothing found in top files (rare), do a broader scan
    if latest is None:
        for p in candidates[:3000]:
            try:
                d = load_json(p)
                di = parse_date_iso(str(d.get("date", "")).strip())
                if di and (latest is None or di > latest):
                    latest = di
            except Exception:
                continue

    return latest


def load_cursor() -> Optional[date]:
    if not CURSOR_PATH.exists():
        return None
    try:
        data = load_json(CURSOR_PATH)
        s = str(data.get("cursor_date", "")).strip()
        return parse_date_iso(s)
    except Exception:
        return None


def save_cursor(d: date) -> None:
    save_json(CURSOR_PATH, {"cursor_date": d.strftime("%Y-%m-%d"), "updated_at_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z"})


def game_type_from_game_id(gameId: str) -> str:
    # NBA gameId prefix:
    # 001 = preseason, 002 = regular season, 003 = all-star (sometimes), 004 = playoffs, 005 = play-in (recent years)
    prefix = gameId[:3]
    return {
        "001": "Preseason",
        "002": "Regular Season",
        "003": "All-Star",
        "004": "Playoffs",
        "005": "Play-In",
    }.get(prefix, "Unknown")


def should_include_game(gameId: str) -> bool:
    gt = game_type_from_game_id(gameId)
    if gt == "Preseason" and not INCLUDE_PRESEASON:
        return False
    # include Regular Season, Playoffs, Play-In by default
    return True


def minutes_to_simple_str(min_str: Any) -> str:
    # Your sample shows "25" not "25:34"
    s = str(min_str or "").strip()
    if not s:
        return ""
    if ":" in s:
        return s.split(":")[0]
    return s


def build_game_json_from_boxscore(box: Dict[str, Any]) -> Dict[str, Any]:
    game = (box.get("game") or {})
    gameId = str(game.get("gameId", "")).strip()

    # date: scoreboard/boxscore provides "gameTimeUTC"
    gameTimeUTC = str(game.get("gameTimeUTC", "")).strip()
    # Example: "2025-10-03T02:00:00Z" -> "2025-10-03"
    date_iso = gameTimeUTC.split("T")[0] if "T" in gameTimeUTC else ""

    home = (game.get("homeTeam") or {})
    away = (game.get("awayTeam") or {})
    arena = (game.get("arena") or {})

    home_name = str(home.get("teamName", "")).strip()
    away_name = str(away.get("teamName", "")).strip()
    home_score = int(home.get("score") or 0)
    away_score = int(away.get("score") or 0)

    winner = ""
    if home_score or away_score:
        if home_score > away_score:
            winner = home_name
        elif away_score > home_score:
            winner = away_name

    attendance = game.get("attendance")
    try:
        attendance_val = int(attendance) if attendance is not None and str(attendance).strip() != "" else None
    except Exception:
        attendance_val = None

    # Players: both teams have a "players" list
    players_out: List[Dict[str, Any]] = []
    for team_obj in (away, home):
        team_name = str(team_obj.get("teamName", "")).strip()
        for p in (team_obj.get("players") or []):
            stats = p.get("statistics") or {}
            if not stats:
                continue

            # Only include players who played (min not empty or points/reb/ast etc)
            min_str = minutes_to_simple_str(stats.get("minutes"))
            played = bool(min_str) or any((stats.get(k) not in (None, "", 0) for k in ("points", "reboundsTotal", "assists")))
            if not played:
                continue

            players_out.append(
                {
                    "player_id": str(p.get("personId", "")).strip(),
                    "player_name": str(p.get("name", "")).strip(),
                    "team": team_name,
                    "minutes": min_str,
                    "points": int(stats.get("points") or 0),
                    "rebounds": int(stats.get("reboundsTotal") or 0),
                    "assists": int(stats.get("assists") or 0),
                    "steals": int(stats.get("steals") or 0),
                    "blocks": int(stats.get("blocks") or 0),
                    "turnovers": int(stats.get("turnovers") or 0),
                    "fouls": int(stats.get("foulsPersonal") or 0),
                    "plus_minus": int(stats.get("plusMinusPoints") or 0),
                    "fg_made": int(stats.get("fieldGoalsMade") or 0),
                    "fg_attempted": int(stats.get("fieldGoalsAttempted") or 0),
                    "three_made": int(stats.get("threePointersMade") or 0),
                    "three_attempted": int(stats.get("threePointersAttempted") or 0),
                    "ft_made": int(stats.get("freeThrowsMade") or 0),
                    "ft_attempted": int(stats.get("freeThrowsAttempted") or 0),
                }
            )

    out = {
        "game_id": safe_int_filename(gameId),
        "season": int(SESSION_FOLDER),
        "date": date_iso,
        "home_team": home_name,
        "away_team": away_name,
        "home_score": home_score,
        "away_score": away_score,
        "winner": winner,
        "game_type": game_type_from_game_id(gameId),
        "game_subtype": "",
        "arena": {
            "arenaId": str(arena.get("arenaId", "")).strip(),
            "arenaName": str(arena.get("arenaName", "")).strip(),
            "arenaCity": str(arena.get("arenaCity", "")).strip(),
            "arenaState": str(arena.get("arenaState", "")).strip(),
        },
        "attendance": attendance_val if attendance_val is not None else 0,
        "players": players_out,
    }
    return out


def list_completed_game_ids_for_date(d: date) -> List[str]:
    url = SCOREBOARD_URL.format(yyyymmdd=yyyymmdd(d))
    data = http_get_json(url)
    games = ((data.get("scoreboard") or {}).get("games") or [])

    game_ids: List[str] = []
    for g in games:
        gid = str(g.get("gameId", "")).strip()
        if not gid:
            continue
        # gameStatus: 1=scheduled, 2=live, 3=final
        status = int(g.get("gameStatus") or 0)
        if status != 3:
            continue
        if not should_include_game(gid):
            continue
        game_ids.append(gid)
    return game_ids


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    latest_existing = find_latest_existing_game_date(OUT_DIR)
    cursor = load_cursor()

    if cursor is None:
        # Start from the day after the latest existing game date (with a backfill buffer)
        if latest_existing is None:
            # If no games exist, start from today - 2 days
            cursor = date.today() - timedelta(days=2)
        else:
            cursor = max(date(1900, 1, 1), latest_existing - timedelta(days=BACKFILL_DAYS))
        save_cursor(cursor)

    start = cursor
    end = min(date.today(), start + timedelta(days=MAX_DAYS_PER_RUN - 1))

    print(f"Season folder: {SESSION_FOLDER}")
    print(f"Latest existing game date (detected): {latest_existing}")
    print(f"Cursor start: {start}  -> end: {end}  (MAX_DAYS_PER_RUN={MAX_DAYS_PER_RUN})")
    print(f"Include preseason: {INCLUDE_PRESEASON}")
    print(f"Max games per run: {MAX_GAMES_PER_RUN}")

    written = 0
    day = start

    while day <= end and written < MAX_GAMES_PER_RUN:
        try:
            completed = list_completed_game_ids_for_date(day)
        except Exception as e:
            print(f"[WARN] Scoreboard fetch failed for {day}: {e}")
            day += timedelta(days=1)
            continue

        if completed:
            print(f"{day}: {len(completed)} completed games")
        else:
            print(f"{day}: 0 completed games")

        for gid in completed:
            if written >= MAX_GAMES_PER_RUN:
                break

            fname = safe_int_filename(gid) + ".json"
            out_path = OUT_DIR / fname

            if out_path.exists():
                continue

            try:
                time.sleep(SLEEP_BETWEEN_CALLS_SEC)
                box = http_get_json(BOXSCORE_URL.format(gameId=gid))
                obj = build_game_json_from_boxscore(box)
                # sanity check: date present
                if not obj.get("date"):
                    print(f"[SKIP] {gid} no date in boxscore payload")
                    continue
                save_json(out_path, obj)
                written += 1
                print(f"[WRITE] {out_path} (gameId={gid})")
            except Exception as e:
                print(f"[WARN] Failed boxscore for {gid}: {e}")

        day += timedelta(days=1)

    # advance cursor to day after 'end'
    next_cursor = end + timedelta(days=1)
    save_cursor(next_cursor)

    print(f"Done. New files written: {written}")
    print(f"Cursor advanced to: {next_cursor}")

    # Exit non-error even if 0 written (that just means no new finals)
    return


if __name__ == "__main__":
    main()
