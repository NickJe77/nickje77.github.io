#!/usr/bin/env python3
"""
generate_nfl_records.py

Scans all player JSON files and builds a single game-records.json
containing the top single-game performances for each stat category.

Output: docs/data/nfl/game-records.json

Run locally:  python generate_nfl_records.py
Run via CI:   see .github/workflows/generate-nfl-records.yml
"""

import json
import os
import sys

# ── Paths ────────────────────────────────────────────────────────────────────
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR     = os.path.join(SCRIPT_DIR, "..", "docs")  # script lives in scripts/, data is in docs/
PLAYERS_DIR  = os.path.join(DOCS_DIR, "data", "nfl", "players")
INDEX_FILE   = os.path.join(DOCS_DIR, "data", "nfl", "players.json")
OUTPUT_FILE  = os.path.join(DOCS_DIR, "data", "nfl", "game-records.json")

# How many records to keep per category
TOP_N = 25

# ── Helpers ──────────────────────────────────────────────────────────────────
TEAM_MAP = {
    "NWE": "NE", "KAN": "KC", "NOR": "NO", "SFO": "SF", "TAM": "TB",
    "SDG": "LAC", "STL": "LAR", "RAI": "LV", "GNB": "GB", "OAK": "LV",
    "PHX": "ARI", "HTX": "HOU", "CLT": "IND",
}

PLAYOFF_WEEKS = {
    # Exact values seen in season JSON files (case-insensitive after stripping)
    "wildcard", "wildcardround",
    "division", "divisional", "divisionalround",
    "confchamp", "nfccg", "afccg", "conferencechampionship", "championship",
    "superbowl", "superbowlgame",
}

def normalize_team(t):
    t = str(t or "").strip().upper()
    return TEAM_MAP.get(t, t)

def is_playoff(week, game_type=""):
    # Strip spaces, hyphens, underscores and lowercase before matching
    w = str(week or "").lower().replace(" ", "").replace("-", "").replace("_", "")
    gt = str(game_type or "").lower()
    return w in PLAYOFF_WEEKS or "playoff" in gt or "post" in gt or "super" in w

def safe_int(v):
    try:
        return int(v or 0)
    except (ValueError, TypeError):
        return 0

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    if not os.path.exists(INDEX_FILE):
        sys.exit(f"ERROR: players index not found at {INDEX_FILE}")
    if not os.path.isdir(PLAYERS_DIR):
        sys.exit(f"ERROR: players directory not found at {PLAYERS_DIR}")

    with open(INDEX_FILE, encoding="utf-8") as f:
        index = json.load(f)

    print(f"Found {len(index)} players in index.")

    all_game_rows = []
    errors = 0

    for i, entry in enumerate(index):
        player_id = entry.get("player_id", "")
        player_file = os.path.join(PLAYERS_DIR, f"{player_id}.json")

        if not os.path.exists(player_file):
            continue

        try:
            with open(player_file, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"  WARN: could not read {player_file}: {e}")
            errors += 1
            continue

        name = data.get("name") or entry.get("name", player_id)

        for g in data.get("games", []):
            s = g.get("stats", {})

            pass_yds = safe_int(s.get("pass_yds"))
            pass_td  = safe_int(s.get("pass_td"))
            pass_att = safe_int(s.get("pass_att"))
            pass_cmp = safe_int(s.get("pass_cmp"))
            pass_int = safe_int(s.get("pass_int"))
            rush_yds = safe_int(s.get("rush_yds"))
            rush_td  = safe_int(s.get("rush_td"))
            rush_att = safe_int(s.get("rush_att"))
            rec_yds  = safe_int(s.get("rec_yds"))
            rec_td   = safe_int(s.get("rec_td"))
            rec      = safe_int(s.get("rec"))

            # Skip if no meaningful stats at all
            if not any([pass_yds, pass_td, rush_yds, rush_td, rec_yds, rec_td, rec]):
                continue

            playoff = is_playoff(g.get("week", ""), g.get("game_type", ""))

            all_game_rows.append({
                "player_id": player_id,
                "name":      name,
                "team":      normalize_team(s.get("team", "")),
                "opponent":  g.get("opponent", ""),
                "season":    safe_int(g.get("season")),
                "date":      g.get("date", ""),
                "game_id":   g.get("game_id", ""),
                "week":      str(g.get("week", "")),
                "playoff":   playoff,
                "pass_yds":  pass_yds,
                "pass_td":   pass_td,
                "pass_att":  pass_att,
                "pass_cmp":  pass_cmp,
                "pass_int":  pass_int,
                "rush_yds":  rush_yds,
                "rush_td":   rush_td,
                "rush_att":  rush_att,
                "rec_yds":   rec_yds,
                "rec_td":    rec_td,
                "rec":       rec,
                "total_yds": pass_yds + rush_yds + rec_yds,
                "total_td":  pass_td  + rush_td  + rec_td,
            })

        if (i + 1) % 500 == 0:
            print(f"  Processed {i + 1} / {len(index)} players...")

    print(f"Total game rows collected: {len(all_game_rows)}  ({errors} file errors)")

    # ── Build top-N lists per category ───────────────────────────────────────
    def top(key, n=TOP_N):
        return sorted(all_game_rows, key=lambda r: r[key], reverse=True)[:n]

    output = {
        "generated":         __import__("datetime").datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_games_indexed": len(all_game_rows),
        "records": {
            "pass_yds":  top("pass_yds"),
            "pass_td":   top("pass_td"),
            "pass_att":  top("pass_att"),
            "pass_int":  top("pass_int"),
            "rush_yds":  top("rush_yds"),
            "rush_td":   top("rush_td"),
            "rush_att":  top("rush_att"),
            "rec_yds":   top("rec_yds"),
            "rec_td":    top("rec_td"),
            "rec":       top("rec"),
            "total_yds": top("total_yds"),
            "total_td":  top("total_td"),
        }
    }

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, separators=(",", ":"))

    size_kb = os.path.getsize(OUTPUT_FILE) / 1024
    print(f"\nDone! Written to: {OUTPUT_FILE}  ({size_kb:.1f} KB)")

if __name__ == "__main__":
    main()
