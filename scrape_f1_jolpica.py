#!/usr/bin/env python3
"""
Scrape F1 data (1950 -> present) from Jolpica (Ergast-compatible) API.

Outputs (JSON) into:
  docs/data/f1/
    seasons.json
    champions_drivers.json
    champions_constructors.json
    seasons/
      1950.json
      1951.json
      ...
Each season file includes:
  - races (calendar + results for all drivers for each round)

Run:
  python3 scrape_f1_jolpica.py
  python3 scrape_f1_jolpica.py --from 1950 --to 2026
  python3 scrape_f1_jolpica.py --from 2000 --to 2026 --only seasons

Notes:
- Uses Jolpica Ergast-compatible API: http://api.jolpi.ca/ergast/f1/
- Polite throttling & retries to reduce 429/503 risk.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import urllib.request
import urllib.error


BASE_URL = "http://api.jolpi.ca/ergast/f1"  # per Jolpica docs
OUT_DIR = os.path.join("docs", "data", "f1")
SEASONS_DIR = os.path.join(OUT_DIR, "seasons")

# Throttling (be polite)
MIN_SECONDS_BETWEEN_REQUESTS = 0.35  # ~3 req/sec, under 4/sec
MAX_RETRIES = 6
BACKOFF_SECONDS = 1.5


@dataclass
class HttpClient:
    last_request_ts: float = 0.0

    def get_json(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = self._build_url(path, params or {})
        self._throttle()
        return self._get_json_with_retries(url)

    def _build_url(self, path: str, params: Dict[str, Any]) -> str:
        # Ensure leading slash
        if not path.startswith("/"):
            path = "/" + path

        # Encode query params
        if params:
            qs = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())
            return f"{BASE_URL}{path}?{qs}"
        return f"{BASE_URL}{path}"

    def _throttle(self) -> None:
        now = time.time()
        elapsed = now - self.last_request_ts
        if elapsed < MIN_SECONDS_BETWEEN_REQUESTS:
            time.sleep(MIN_SECONDS_BETWEEN_REQUESTS - elapsed)
        self.last_request_ts = time.time()

    def _get_json_with_retries(self, url: str) -> Dict[str, Any]:
        for attempt in range(MAX_RETRIES):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "SportingAlmanacBot/1.0"})
                with urllib.request.urlopen(req, timeout=30) as resp:
                    raw = resp.read().decode("utf-8")
                    return json.loads(raw)
            except urllib.error.HTTPError as e:
                code = getattr(e, "code", None)
                # 429 Too Many Requests / 503 Backend issues
                if code in (429, 500, 502, 503, 504):
                    sleep_for = BACKOFF_SECONDS * (attempt + 1)
                    time.sleep(sleep_for)
                    continue
                raise
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
                sleep_for = BACKOFF_SECONDS * (attempt + 1)
                time.sleep(sleep_for)
                continue
        raise RuntimeError(f"Failed to fetch after retries: {url}")


def ensure_dirs() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(SEASONS_DIR, exist_ok=True)


def write_json(path: str, obj: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def safe_int(x: Any) -> Optional[int]:
    try:
        return int(x)
    except Exception:
        return None


def get_seasons(client: HttpClient) -> List[int]:
    # Ergast-style endpoint: /seasons.json
    data = client.get_json("/seasons.json", params={"limit": 1000, "offset": 0})
    seasons = data.get("MRData", {}).get("SeasonTable", {}).get("Seasons", [])
    years: List[int] = []
    for s in seasons:
        y = safe_int(s.get("season"))
        if y is not None:
            years.append(y)
    years = sorted(set(years))
    return years


def get_driver_champion(client: HttpClient, season: int) -> Optional[Dict[str, Any]]:
    # /{season}/driverStandings/1.json
    data = client.get_json(f"/{season}/driverStandings/1.json", params={"limit": 1000})
    lists = data.get("MRData", {}).get("StandingsTable", {}).get("StandingsLists", [])
    if not lists:
        return None
    sl = lists[0]
    standings = sl.get("DriverStandings", [])
    if not standings:
        return None
    top = standings[0]
    d = top.get("Driver", {})
    constructors = top.get("Constructors", [])
    constructor_name = constructors[0].get("name") if constructors else None
    return {
        "season": str(season),
        "driverId": d.get("driverId"),
        "givenName": d.get("givenName"),
        "familyName": d.get("familyName"),
        "code": d.get("code"),
        "nationality": d.get("nationality"),
        "constructor": constructor_name,
        "points": top.get("points"),
        "wins": top.get("wins"),
    }


def get_constructor_champion(client: HttpClient, season: int) -> Optional[Dict[str, Any]]:
    # /{season}/constructorStandings/1.json
    data = client.get_json(f"/{season}/constructorStandings/1.json", params={"limit": 1000})
    lists = data.get("MRData", {}).get("StandingsTable", {}).get("StandingsLists", [])
    if not lists:
        return None
    sl = lists[0]
    standings = sl.get("ConstructorStandings", [])
    if not standings:
        return None
    top = standings[0]
    c = top.get("Constructor", {})
    return {
        "season": str(season),
        "constructorId": c.get("constructorId"),
        "name": c.get("name"),
        "nationality": c.get("nationality"),
        "points": top.get("points"),
        "wins": top.get("wins"),
    }


def get_race_calendar(client: HttpClient, season: int) -> List[Dict[str, Any]]:
    # /{season}.json gives the race list
    data = client.get_json(f"/{season}.json", params={"limit": 1000})
    races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
    return races or []


def get_race_results_all_drivers(client: HttpClient, season: int, round_no: str) -> List[Dict[str, Any]]:
    # /{season}/{round}/results.json returns all classified results (all drivers)
    data = client.get_json(f"/{season}/{round_no}/results.json", params={"limit": 500, "offset": 0})
    races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
    if not races:
        return []
    results = races[0].get("Results", []) or []
    return results


def build_season_file(client: HttpClient, season: int) -> Dict[str, Any]:
    races = get_race_calendar(client, season)
    out_races: List[Dict[str, Any]] = []

    for r in races:
        round_no = str(r.get("round"))
        results = get_race_results_all_drivers(client, season, round_no)

        out_races.append({
            "season": str(season),
            "round": round_no,
            "raceName": r.get("raceName"),
            "date": r.get("date"),
            "time": r.get("time"),
            "url": r.get("url"),
            "circuit": {
                "circuitId": (r.get("Circuit") or {}).get("circuitId"),
                "circuitName": (r.get("Circuit") or {}).get("circuitName"),
                "locality": ((r.get("Circuit") or {}).get("Location") or {}).get("locality"),
                "country": ((r.get("Circuit") or {}).get("Location") or {}).get("country"),
                "lat": ((r.get("Circuit") or {}).get("Location") or {}).get("lat"),
                "long": ((r.get("Circuit") or {}).get("Location") or {}).get("long"),
            },
            "results": [{
                "position": res.get("position"),
                "positionText": res.get("positionText"),
                "points": res.get("points"),
                "grid": res.get("grid"),
                "laps": res.get("laps"),
                "status": res.get("status"),
                "time": (res.get("Time") or {}).get("time"),
                "fastestLap": res.get("FastestLap"),
                "driver": {
                    "driverId": (res.get("Driver") or {}).get("driverId"),
                    "givenName": (res.get("Driver") or {}).get("givenName"),
                    "familyName": (res.get("Driver") or {}).get("familyName"),
                    "code": (res.get("Driver") or {}).get("code"),
                    "number": (res.get("Driver") or {}).get("permanentNumber") or (res.get("Driver") or {}).get("number"),
                    "nationality": (res.get("Driver") or {}).get("nationality"),
                },
                "constructor": {
                    "constructorId": (res.get("Constructor") or {}).get("constructorId"),
                    "name": (res.get("Constructor") or {}).get("name"),
                    "nationality": (res.get("Constructor") or {}).get("nationality"),
                }
            } for res in results]
        })

    return {
        "season": str(season),
        "races": out_races
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--from", dest="year_from", type=int, default=1950)
    parser.add_argument("--to", dest="year_to", type=int, default=None,
                        help="inclusive end year (default: current year)")
    parser.add_argument("--only", dest="only", choices=["all", "seasons", "champions"], default="all",
                        help="what to scrape")
    args = parser.parse_args()

    ensure_dirs()
    client = HttpClient()

    current_year = time.gmtime().tm_year
    year_to = args.year_to if args.year_to is not None else current_year

    # 1) Seasons list from API
    all_years = get_seasons(client)
    years = [y for y in all_years if args.year_from <= y <= year_to]

    write_json(os.path.join(OUT_DIR, "seasons.json"), {
        "from": args.year_from,
        "to": year_to,
        "seasons": years
    })

    if args.only in ("all", "champions"):
        drivers_champs: List[Dict[str, Any]] = []
        constructors_champs: List[Dict[str, Any]] = []

        for y in years:
            dc = get_driver_champion(client, y)
            if dc:
                drivers_champs.append(dc)

            cc = get_constructor_champion(client, y)
            if cc:
                constructors_champs.append(cc)

        write_json(os.path.join(OUT_DIR, "champions_drivers.json"), drivers_champs)
        write_json(os.path.join(OUT_DIR, "champions_constructors.json"), constructors_champs)

    if args.only in ("all", "seasons"):
        for y in years:
            out_path = os.path.join(SEASONS_DIR, f"{y}.json")
            season_obj = build_season_file(client, y)
            write_json(out_path, season_obj)
            print(f"Wrote {out_path} ({len(season_obj.get('races', []))} races)")

    print("Done.")


if __name__ == "__main__":
    main()
