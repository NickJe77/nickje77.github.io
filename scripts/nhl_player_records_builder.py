#!/usr/bin/env python3
"""
NHL Player Records Builder

Scans every file in docs/data/nhl/players/ and computes all-time and
single-season player records. Pre-generated because computing this
client-side from thousands of player files would be too slow.

Output: docs/data/nhl/player-records.json
"""

import json
from pathlib import Path

PLAYERS_DIR = Path("docs/data/nhl/players")
INDEX_FILE  = Path("docs/data/nhl/players.json")
OUT_FILE    = Path("docs/data/nhl/player-records.json")

# Load player names/positions
player_info = {}
if INDEX_FILE.exists():
    for p in json.loads(INDEX_FILE.read_text()):
        player_info[p["id"]] = p

files = sorted(PLAYERS_DIR.glob("*.json"))
print(f"Found {len(files)} player files")

career_totals  = []  # one row per player: career sums
season_totals  = []  # one row per player-season
single_games   = []  # every individual game (for single-game records)

for i, f in enumerate(files):
    pid = f.stem
    try:
        games = json.loads(f.read_text())
    except Exception:
        continue
    if not games:
        continue

    info = player_info.get(pid, {})
    name = info.get("name", pid)
    pos  = info.get("position", "")
    is_goalie = pos == "G"

    # Career aggregation
    c_gp=0; c_goals=0; c_assists=0; c_points=0; c_pim=0; c_shots=0; c_hits=0
    c_ppg=0; c_blocked=0
    seen = set()

    # Season aggregation: key = season
    season_map = {}

    for g in games:
        gid = str(g.get("game_id")) + "|" + str(g.get("team"))
        if gid in seen:
            continue
        seen.add(gid)

        season = g.get("season")
        goals  = g.get("goals", 0) or 0
        assists= g.get("assists", 0) or 0
        points = g.get("points", 0) or (goals + assists)
        pim    = g.get("pim", 0) or 0
        shots  = g.get("shots", 0) or 0
        hits   = g.get("hits", 0) or 0
        ppg    = g.get("pp_goals", 0) or 0
        blocked= g.get("blocked", 0) or 0

        c_gp += 1
        c_goals += goals; c_assists += assists; c_points += points
        c_pim += pim; c_shots += shots; c_hits += hits
        c_ppg += ppg; c_blocked += blocked

        if season is not None:
            if season not in season_map:
                season_map[season] = {"gp":0,"goals":0,"assists":0,"points":0,
                                       "pim":0,"shots":0,"hits":0,"ppg":0,
                                       "team": g.get("team","")}
            sm = season_map[season]
            sm["gp"] += 1
            sm["goals"] += goals; sm["assists"] += assists; sm["points"] += points
            sm["pim"] += pim; sm["shots"] += shots; sm["hits"] += hits
            sm["ppg"] += ppg
            sm["team"] = g.get("team", sm["team"])

        # Single game record (skip goalies for offensive single-game records)
        if not is_goalie:
            single_games.append({
                "id": pid, "name": name, "team": g.get("team",""),
                "season": season, "game_id": g.get("game_id"),
                "goals": goals, "assists": assists, "points": points,
            })

    if not is_goalie and c_gp > 0:
        career_totals.append({
            "id": pid, "name": name, "position": pos,
            "gp": c_gp, "goals": c_goals, "assists": c_assists, "points": c_points,
            "pim": c_pim, "shots": c_shots, "hits": c_hits, "ppg": c_ppg,
            "blocked": c_blocked,
        })

        for season, sm in season_map.items():
            season_totals.append({
                "id": pid, "name": name, "season": season, "team": sm["team"],
                "gp": sm["gp"], "goals": sm["goals"], "assists": sm["assists"],
                "points": sm["points"], "pim": sm["pim"], "shots": sm["shots"],
                "hits": sm["hits"], "ppg": sm["ppg"],
            })

    if (i+1) % 1000 == 0:
        print(f"  [{i+1}/{len(files)}] processed")

print(f"\nCareer totals: {len(career_totals)} players")
print(f"Season totals: {len(season_totals)} player-seasons")
print(f"Single games: {len(single_games)} games")

# Build top-10 lists for each record category
def top10(data, key, reverse=True):
    return sorted(data, key=lambda x: x.get(key, 0), reverse=reverse)[:10]

records = {
    "career": {
        "goals":   top10(career_totals, "goals"),
        "assists": top10(career_totals, "assists"),
        "points":  top10(career_totals, "points"),
        "pim":     top10(career_totals, "pim"),
        "hits":    top10(career_totals, "hits"),
        "shots":   top10(career_totals, "shots"),
        "games":   top10(career_totals, "gp"),
        "ppg":     top10(career_totals, "ppg"),
    },
    "season": {
        "goals":   top10(season_totals, "goals"),
        "assists": top10(season_totals, "assists"),
        "points":  top10(season_totals, "points"),
        "pim":     top10(season_totals, "pim"),
        "hits":    top10(season_totals, "hits"),
        "ppg":     top10(season_totals, "ppg"),
    },
    "single_game": {
        "goals":   top10(single_games, "goals"),
        "assists": top10(single_games, "assists"),
        "points":  top10(single_games, "points"),
    },
}

OUT_FILE.write_text(json.dumps(records, separators=(",", ":")))
print(f"\nSaved {OUT_FILE}")
