#!/usr/bin/env python3
"""
Build per-game NBA JSON files from a Kaggle dataset folder.

Expected output:
  docs/data/nba/<season>/index.json
  docs/data/nba/<season>/<game_id>.json

This script tries hard to auto-detect the correct CSVs even if filenames differ.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd


def _norm_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df


def _find_csvs(dataset_dir: Path) -> List[Path]:
    return sorted([p for p in dataset_dir.rglob("*.csv") if p.is_file()])


def _score_games_csv(cols: set) -> int:
    """
    Heuristic score to identify the "games" CSV.
    """
    score = 0
    must_any = [{"game_id", "gameid"}, {"home_team", "home"}, {"away_team", "away"}]
    for s in must_any:
        if cols.intersection(s):
            score += 3

    # date-ish
    if cols.intersection({"date", "game_date", "gamedate", "game_date_est"}):
        score += 3

    # points/scores
    if cols.intersection({"home_score", "home_points", "pts_home", "home_pts"}):
        score += 2
    if cols.intersection({"away_score", "away_points", "pts_away", "away_pts"}):
        score += 2

    # season / year
    if cols.intersection({"season", "year"}):
        score += 2

    # season type
    if cols.intersection({"season_type", "game_type", "type"}):
        score += 1

    return score


def _score_box_csv(cols: set) -> int:
    """
    Heuristic score to identify the player box score CSV.
    """
    score = 0
    # must have game + player
    if cols.intersection({"game_id", "gameid"}):
        score += 4
    if cols.intersection({"player_id", "playerid"}):
        score += 4

    # typical stat fields
    stat_fields = {
        "pts", "points",
        "reb", "rebounds",
        "ast", "assists",
        "stl", "steals",
        "blk", "blocks",
        "tov", "turnovers",
        "min", "minutes",
        "fgm", "fga",
        "fg3m", "fg3a",
        "ftm", "fta",
        "plus_minus", "+/-",
        "team", "team_name", "team_abbreviation",
    }
    score += len(cols.intersection(stat_fields))

    return score


def _read_csv_fast(path: Path) -> pd.DataFrame:
    # low_memory=False to reduce dtype chaos; keep as strings where needed later.
    return pd.read_csv(path, low_memory=False)


def _pick_best_csvs(csvs: List[Path]) -> Tuple[Path, Path]:
    """
    Returns (games_csv, box_csv)
    """
    best_games = None
    best_games_score = -1

    best_box = None
    best_box_score = -1

    # Only read headers first (cheap)
    for p in csvs:
        try:
            head = pd.read_csv(p, nrows=5, low_memory=False)
            head = _norm_cols(head)
            cols = set(head.columns)

            gs = _score_games_csv(cols)
            bs = _score_box_csv(cols)

            if gs > best_games_score:
                best_games_score = gs
                best_games = p

            if bs > best_box_score:
                best_box_score = bs
                best_box = p
        except Exception:
            continue

    if not best_games or not best_box:
        raise SystemExit(
            "Could not auto-detect CSV files. "
            "Make sure the dataset folder contains the games + player box score CSVs."
        )

    return best_games, best_box


def _get_col(df: pd.DataFrame, options: List[str]) -> Optional[str]:
    cols = set(df.columns)
    for o in options:
        if o in cols:
            return o
    return None


def _safe_int(x) -> Optional[int]:
    try:
        if pd.isna(x):
            return None
        return int(float(x))
    except Exception:
        return None


def _safe_str(x) -> str:
    if pd.isna(x):
        return ""
    return str(x)


def _parse_date(s: str) -> str:
    # Return ISO date (YYYY-MM-DD) if possible
    s = _safe_str(s).strip()
    if not s:
        return ""
    try:
        dt = pd.to_datetime(s, errors="coerce", utc=False)
        if pd.isna(dt):
            return ""
        return dt.date().isoformat()
    except Exception:
        return ""


def _infer_season_from_date(date_iso: str) -> Optional[int]:
    """
    If season missing, infer: NBA season year = year of the season END (like your folders).
    Eg 2024-11-01 is 2025 season.
    """
    if not date_iso:
        return None
    try:
        y = int(date_iso[:4])
        m = int(date_iso[5:7])
        return y + 1 if m >= 7 else y
    except Exception:
        return None


def _is_preseason(row: Dict, season_type_val: str) -> bool:
    v = (season_type_val or "").strip().lower()
    if not v:
        # if unknown, assume NOT preseason
        return False
    # common labels
    if "pre" in v and "season" in v:
        return True
    if v in {"preseason", "pre-season"}:
        return True
    return False


def _is_regular_or_playoffs(season_type_val: str) -> bool:
    v = (season_type_val or "").strip().lower()
    if not v:
        return True  # default to keep
    if "regular" in v:
        return True
    if "playoff" in v or "postseason" in v:
        return True
    if v in {"rs", "po"}:
        return True
    # explicitly exclude
    if "pre" in v:
        return False
    return True


def build(dataset_dir: Path, out_root: Path, start_season: int, end_season: int, overwrite: bool) -> None:
    csvs = _find_csvs(dataset_dir)
    if not csvs:
        raise SystemExit(f"No CSV files found under: {dataset_dir}")

    games_csv, box_csv = _pick_best_csvs(csvs)
    print(f"Detected games CSV: {games_csv}")
    print(f"Detected box CSV:   {box_csv}")

    games = _norm_cols(_read_csv_fast(games_csv))
    box = _norm_cols(_read_csv_fast(box_csv))

    # Identify key columns in games
    col_game_id = _get_col(games, ["game_id", "gameid"])
    if not col_game_id:
        raise SystemExit("Games CSV has no game_id column (game_id/gameId).")

    col_date = _get_col(games, ["date", "game_date", "gamedate", "game_date_est"])
    col_season = _get_col(games, ["season", "year"])
    col_home = _get_col(games, ["home_team", "home", "home_team_name"])
    col_away = _get_col(games, ["away_team", "away", "visitor_team", "away_team_name"])
    col_home_pts = _get_col(games, ["home_score", "home_points", "pts_home", "home_pts"])
    col_away_pts = _get_col(games, ["away_score", "away_points", "pts_away", "away_pts"])
    col_type = _get_col(games, ["season_type", "game_type", "type"])

    # Identify key columns in box
    b_game_id = _get_col(box, ["game_id", "gameid"])
    b_player_id = _get_col(box, ["player_id", "playerid"])
    b_player_name = _get_col(box, ["player_name", "name", "player"])
    b_team = _get_col(box, ["team", "team_name", "team_abbreviation", "team_abbr"])

    if not (b_game_id and b_player_id):
        raise SystemExit("Box CSV missing game_id and/or player_id columns.")

    # Normalize game_id as string for joining
    games[col_game_id] = games[col_game_id].astype(str)
    box[b_game_id] = box[b_game_id].astype(str)
    if b_player_id:
        box[b_player_id] = box[b_player_id].astype(str)

    # Helpful: map box rows by game_id
    box_by_game: Dict[str, pd.DataFrame] = dict(tuple(box.groupby(b_game_id, sort=False)))

    written = 0
    kept = 0
    skipped = 0

    # Iterate games
    for _, g in games.iterrows():
        game_id = str(g.get(col_game_id, "")).strip()
        if not game_id:
            continue

        date_iso = _parse_date(g.get(col_date, "")) if col_date else ""
        season_val = _safe_int(g.get(col_season)) if col_season else None
        if not season_val:
            season_val = _infer_season_from_date(date_iso)

        if not season_val:
            continue

        if season_val < start_season or season_val > end_season:
            continue

        season_type_val = _safe_str(g.get(col_type, "")) if col_type else ""
        if not _is_regular_or_playoffs(season_type_val):
            skipped += 1
            continue

        home_team = _safe_str(g.get(col_home, "")) if col_home else ""
        away_team = _safe_str(g.get(col_away, "")) if col_away else ""

        home_score = _safe_int(g.get(col_home_pts)) if col_home_pts else None
        away_score = _safe_int(g.get(col_away_pts)) if col_away_pts else None

        winner = ""
        if home_score is not None and away_score is not None and home_team and away_team:
            if home_score > away_score:
                winner = home_team
            elif away_score > home_score:
                winner = away_team

        # Players
        players: List[Dict] = []
        gbox = box_by_game.get(game_id)
        if gbox is not None:
            # Build a players list with lots of common columns if present
            # We'll include anything from a "known" set if it exists
            known = [
                ("minutes", ["min", "minutes"]),
                ("points", ["pts", "points"]),
                ("rebounds", ["reb", "rebounds"]),
                ("assists", ["ast", "assists"]),
                ("steals", ["stl", "steals"]),
                ("blocks", ["blk", "blocks"]),
                ("turnovers", ["tov", "turnovers"]),
                ("fouls", ["pf", "fouls", "personal_fouls"]),
                ("fgm", ["fgm"]),
                ("fga", ["fga"]),
                ("fg3m", ["fg3m"]),
                ("fg3a", ["fg3a"]),
                ("ftm", ["ftm"]),
                ("fta", ["fta"]),
                ("plus_minus", ["plus_minus", "+/-"]),
            ]

            # Resolve actual column names
            gbox_cols = set(gbox.columns)
            resolved = []
            for out_key, opts in known:
                c = None
                for o in opts:
                    if o in gbox_cols:
                        c = o
                        break
                resolved.append((out_key, c))

            for _, r in gbox.iterrows():
                pid = _safe_str(r.get(b_player_id, "")).strip()
                pname = _safe_str(r.get(b_player_name, "")).strip() if b_player_name else ""
                team = _safe_str(r.get(b_team, "")).strip() if b_team else ""

                if not pid and not pname:
                    continue

                row = {
                    "player_id": pid,
                    "player_name": pname,
                    "team": team,
                }

                for out_key, c in resolved:
                    if c:
                        v = r.get(c)
                        # keep minutes as string sometimes
                        if out_key == "minutes":
                            row[out_key] = _safe_str(v).strip()
                        else:
                            row[out_key] = _safe_int(v) if v is not None else None

                players.append(row)

        out_dir = out_root / str(season_val)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{game_id}.json"

        if out_path.exists() and not overwrite:
            kept += 1
            continue

        game_obj = {
            "game_id": game_id,
            "season": season_val,
            "date": date_iso,
            "home_team": home_team,
            "away_team": away_team,
            "home_score": home_score if home_score is not None else 0,
            "away_score": away_score if away_score is not None else 0,
            "winner": winner,
            # Kaggle may not have these; keep structure compatible with your site
            "game_type": "Playoffs" if "playoff" in season_type_val.lower() else "Regular Season",
            "game_subtype": "",
            "arena": {
                "arenaId": "",
                "arenaName": "",
                "arenaCity": "",
                "arenaState": ""
            },
            "attendance": 0,
            "players": players
        }

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(game_obj, f, ensure_ascii=False, indent=2)

        written += 1

    # Build season index.json (list all game files for each season)
    for season in range(start_season, end_season + 1):
        season_dir = out_root / str(season)
        if not season_dir.exists():
            continue

        game_files = sorted([p for p in season_dir.glob("*.json") if p.name != "index.json"])
        if not game_files:
            continue

        # Sort by date if possible
        items = []
        for p in game_files:
            try:
                d = json.load(open(p, "r", encoding="utf-8"))
                items.append((d.get("date", ""), d.get("game_id", p.stem)))
            except Exception:
                items.append(("", p.stem))

        items.sort(key=lambda x: (x[0] or "", x[1]))

        index_obj = {"season": season, "games": [gid for _, gid in items]}
        with open(season_dir / "index.json", "w", encoding="utf-8") as f:
            json.dump(index_obj, f, ensure_ascii=False, indent=2)

    print("\nDONE")
    print(f"New games written: {written}")
    print(f"Already existed (kept): {kept}")
    print(f"Skipped (preseason/filtered): {skipped}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True, help="Path to Kaggle dataset folder (unzipped).")
    ap.add_argument("--out", default="docs/data/nba", help="Output root (default: docs/data/nba).")
    ap.add_argument("--start", type=int, default=1976, help="Start season folder year (default: 1976).")
    ap.add_argument("--end", type=int, default=2025, help="End season folder year (default: 2025).")
    ap.add_argument("--overwrite", action="store_true", help="Overwrite existing game JSON files.")
    args = ap.parse_args()

    dataset_dir = Path(args.dataset).resolve()
    out_root = Path(args.out).resolve()

    if not dataset_dir.exists():
        raise SystemExit(f"Dataset path does not exist: {dataset_dir}")

    build(dataset_dir, out_root, args.start, args.end, args.overwrite)


if __name__ == "__main__":
    main()
