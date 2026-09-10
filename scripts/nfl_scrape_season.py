#!/usr/bin/env python3
"""
nfl_scrape_season.py  (ESPN-backed version)

Replaces the old pro-football-reference.com scraper, which got blocked by
Cloudflare's bot challenge when run from GitHub Actions' datacenter IPs.
ESPN's public site.api.espn.com endpoints return plain JSON with no bot
wall, so this version pulls the same data from there instead.

Output schema is UNCHANGED from before, so nothing downstream
(build_nfl_players.py, nfl-seasons.html, nfl-game.html, nfl-leaders.html,
nfl-head2head.html) needs to change:

  docs/data/nfl/seasons/{season}.json
      { "season": int, "source": url, "updated": iso timestamp,
        "games": [ { "game_id", "date", "week", "team1", "team2",
                     "score1", "score2", "venue" }, ... ] }

  docs/data/nfl/boxscores/{season}/{game_id}.json
      { "game_id": str,
        "passing": [ {"player": name, "stats": {...}}, ... ],
        "rushing": [...], "receiving": [...], "defense": [...],
        "kicking": [...], "returns": [...], "scoring": [...] }

Usage:
    python3 scripts/nfl_scrape_season.py 2026

Only fetches boxscores for games ESPN marks as completed, and skips any
boxscore file that's already on disk, so it's safe to re-run weekly.
"""

import json
import os
import sys
import time
import datetime as dt

import requests

BASE = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"

OUT_ROOT = "docs/data/nfl"
SEASONS_DIR = f"{OUT_ROOT}/seasons"
BOXSCORE_DIR = f"{OUT_ROOT}/boxscores"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36",
    "Accept": "application/json",
}

session = requests.Session()
session.headers.update(HEADERS)

# seasontype: 1=preseason, 2=regular, 3=postseason
# (weeks, seasontype) pairs to sweep for a full season
REGULAR_WEEKS = list(range(1, 19))          # weeks 1-18
POSTSEASON_WEEKS = list(range(1, 6))        # wildcard..superbowl (incl. pro bowl slot)

# ESPN boxscore stat-group names -> our schema buckets
GROUP_MAP = {
    "passing": "passing",
    "rushing": "rushing",
    "receiving": "receiving",
    "fumbles": "defense",
    "defensive": "defense",
    "interceptions": "defense",
    "kicking": "kicking",
    "punting": "kicking",
    "kickReturns": "returns",
    "puntReturns": "returns",
}


def fetch_json(url, retries=4):
    for i in range(retries):
        try:
            res = session.get(url, timeout=30)
            if res.status_code == 200:
                try:
                    return res.json()
                except ValueError:
                    print(f"  bad JSON from {url}")
                    return None
            if res.status_code == 404:
                return None
            print(f"  HTTP {res.status_code} from {url}, retrying ({i+1}/{retries})...")
        except requests.RequestException as e:
            print(f"  request error: {e}, retrying ({i+1}/{retries})...")
        time.sleep(3 + i * 2)
    return None


def parse_score(competitor):
    val = competitor.get("score")
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def get_week_games(season, seasontype, week):
    url = f"{BASE}/scoreboard?dates={season}&seasontype={seasontype}&week={week}"
    data = fetch_json(url)
    if not data:
        return []

    games = []
    for event in data.get("events", []):
        try:
            comps = event["competitions"][0]
            competitors = comps["competitors"]
            home = next(c for c in competitors if c.get("homeAway") == "home")
            away = next(c for c in competitors if c.get("homeAway") == "away")
            completed = comps.get("status", {}).get("type", {}).get("completed", False)

            games.append({
                "game_id": str(event["id"]),
                "date": event.get("date", "")[:10],
                "week": week,
                "team1": away.get("team", {}).get("displayName", ""),
                "team2": home.get("team", {}).get("displayName", ""),
                "score1": parse_score(away) if completed else None,
                "score2": parse_score(home) if completed else None,
                "venue": comps.get("venue", {}).get("fullName", ""),
                "_completed": completed,
            })
        except (KeyError, IndexError, StopIteration):
            continue

    return games


def get_season_schedule(season):
    all_games = []
    for week in REGULAR_WEEKS:
        print(f"Fetching regular season week {week}...")
        games = get_week_games(season, 2, week)
        print(f"  found {len(games)} games")
        all_games.extend(games)

    for week in POSTSEASON_WEEKS:
        print(f"Fetching postseason week {week}...")
        games = get_week_games(season, 3, week)
        print(f"  found {len(games)} games")
        all_games.extend(games)

    return all_games


def scrape_boxscore(game_id):
    url = f"{BASE}/summary?event={game_id}"
    data = fetch_json(url)
    if not data:
        return None

    out = {
        "game_id": game_id,
        "passing": [], "rushing": [], "receiving": [],
        "defense": [], "kicking": [], "returns": [], "scoring": [],
    }

    boxscore = data.get("boxscore", {})
    for team_block in boxscore.get("players", []):
        team_abbrev = team_block.get("team", {}).get("abbreviation", "")
        for stat_group in team_block.get("statistics", []):
            group_name = stat_group.get("name") or stat_group.get("displayName", "")
            bucket = GROUP_MAP.get(group_name)
            if not bucket:
                continue
            labels = stat_group.get("labels", [])
            for athlete in stat_group.get("athletes", []):
                try:
                    name = athlete["athlete"]["displayName"]
                except KeyError:
                    continue
                stats = dict(zip(labels, athlete.get("stats", [])))
                stats["team"] = team_abbrev
                out[bucket].append({"player": name, "stats": stats})

    for play in data.get("scoringPlays", []):
        out["scoring"].append({
            "quarter": play.get("period", {}).get("number", ""),
            "team": play.get("team", {}).get("abbreviation", ""),
            "scorer": play.get("text", ""),
            "type": play.get("type", {}).get("text", ""),
            "description": play.get("text", ""),
        })

    return out


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/nfl_scrape_season.py <season>")
        sys.exit(1)

    season = int(sys.argv[1])

    os.makedirs(SEASONS_DIR, exist_ok=True)
    box_dir = f"{BOXSCORE_DIR}/{season}"
    os.makedirs(box_dir, exist_ok=True)

    games = get_season_schedule(season)

    clean_games = [{k: v for k, v in g.items() if not k.startswith("_")} for g in games]
    season_out = {
        "season": season,
        "source": f"{BASE}/scoreboard",
        "updated": dt.datetime.utcnow().isoformat() + "Z",
        "games": clean_games,
    }
    with open(f"{SEASONS_DIR}/{season}.json", "w", encoding="utf-8") as f:
        json.dump(season_out, f, indent=2, ensure_ascii=False)
    print(f"\nWrote {SEASONS_DIR}/{season}.json ({len(clean_games)} games)")

    played = [g for g in games if g.get("_completed")]
    print(f"{len(played)} games completed / have boxscores available")

    fetched, skipped, failed = 0, 0, 0
    for g in played:
        out_path = f"{box_dir}/{g['game_id']}.json"
        if os.path.exists(out_path):
            skipped += 1
            continue

        print(f"Fetching boxscore: {g['game_id']} ({g['team1']} @ {g['team2']})")
        box = scrape_boxscore(g["game_id"])
        if not box:
            print("  FAILED")
            failed += 1
            continue

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(box, f, indent=2, ensure_ascii=False)
        fetched += 1
        time.sleep(1)

    print(f"\nDone. fetched={fetched} skipped(existing)={skipped} failed={failed}")


if __name__ == "__main__":
    main()
