#!/usr/bin/env python3
"""
Patch UCL match files:
1. Fill blank team fields using home_lineup / away_lineup
2. Normalise all team names using TEAM_NAME_MAP
"""
import json
import os
import sys
from pathlib import Path

MATCH_DIR = Path("docs/data/ucl/matches")

TEAM_NAME_MAP = {
    "Man Utd":                    "Manchester United",
    "Man United":                 "Manchester United",
    "B. Dortmund":                "Borussia Dortmund",
    "Dortmund":                   "Borussia Dortmund",
    "Bayern":                     "Bayern Munich",
    "FC Bayern":                  "Bayern Munich",
    "FC Bayern Munich":           "Bayern Munich",
    "B. Munich":                  "Bayern Munich",
    "Paris":                      "Paris Saint-Germain",
    "PSG":                        "Paris Saint-Germain",
    "Inter":                      "Internazionale",
    "Inter Milan":                "Internazionale",
    "FC Internazionale":          "Internazionale",
    "Atletico":                   "Atletico Madrid",
    "Atletico Madrid":            "Atletico Madrid",
    "Atlético Madrid":            "Atletico Madrid",
    "Atlético":                   "Atletico Madrid",
    "S. Bratislava":              "Slovan Bratislava",
    "Crvena Zvezda":              "Red Star Belgrade",
    "FK Crvena zvezda":           "Red Star Belgrade",
    "Milan":                      "AC Milan",
    "Juventus FC":                "Juventus",
    "FCB":                        "Barcelona",
    "FC Barcelona":               "Barcelona",
    "Real":                       "Real Madrid",
    "FC Porto":                   "Porto",
    "FC Valencia":                "Valencia",
    "Bayer Leverkusen":           "Leverkusen",
    "Bayer 04":                   "Leverkusen",
    "Olympique Lyon":             "Lyon",
    "Olympique de Marseille":     "Marseille",
    "AS Roma":                    "Roma",
    "SS Lazio":                   "Lazio",
    "ACF Fiorentina":             "Fiorentina",
    "AFC Ajax":                   "Ajax",
    "PSV":                        "PSV Eindhoven",
    "Sporting":                   "Sporting CP",
    "Sporting Lisbon":            "Sporting CP",
    "Zenit":                      "Zenit St. Petersburg",
    "RB Salzburg":                "Red Bull Salzburg",
    "Shakhtar":                   "Shakhtar Donetsk",
    "Celtic FC":                  "Celtic",
    "Rangers FC":                 "Rangers",
    "SL Benfica":                 "Benfica",
    "Galatasaray SK":             "Galatasaray",
    "Club Brugge KV":             "Club Brugge",
}


def normalise(name: str) -> str:
    name = (name or "").strip()
    return TEAM_NAME_MAP.get(name, name)


def patch_file(path: Path) -> bool:
    with open(path, encoding="utf-8") as f:
        match = json.load(f)

    changed = False

    # Normalise home/away team names
    for key in ("home_team", "away_team", "home", "away"):
        if key in match:
            normed = normalise(match[key])
            if normed != match[key]:
                match[key] = normed
                changed = True

    home_team = normalise(match.get("home_team") or match.get("home") or "")
    away_team = normalise(match.get("away_team") or match.get("away") or "")

    # Build lineup map
    lineup_map = {}
    for player in match.get("home_lineup") or []:
        if player:
            lineup_map[player.strip()] = home_team
    for player in match.get("away_lineup") or []:
        if player:
            lineup_map[player.strip()] = away_team

    # Patch scorers
    for event in match.get("scorers") or []:
        raw = (event.get("team") or "").strip()
        normed = normalise(raw)
        if normed != raw:
            event["team"] = normed
            changed = True
        if not event.get("team"):
            player = (event.get("player") or "").strip()
            if player in lineup_map:
                event["team"] = lineup_map[player]
                changed = True

    # Patch yellow cards
    for event in match.get("yellow_cards") or []:
        raw = (event.get("team") or "").strip()
        normed = normalise(raw)
        if normed != raw:
            event["team"] = normed
            changed = True
        if not event.get("team"):
            player = (event.get("player") or "").strip()
            if player in lineup_map:
                event["team"] = lineup_map[player]
                changed = True

    # Patch red cards
    for event in match.get("red_cards") or []:
        raw = (event.get("team") or "").strip()
        normed = normalise(raw)
        if normed != raw:
            event["team"] = normed
            changed = True
        if not event.get("team"):
            player = (event.get("player") or "").strip()
            if player in lineup_map:
                event["team"] = lineup_map[player]
                changed = True

    if changed:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(match, f, indent=2, ensure_ascii=False)

    return changed


def main():
    if not MATCH_DIR.exists():
        print(f"Match directory not found: {MATCH_DIR}", file=sys.stderr)
        sys.exit(1)

    files = sorted(MATCH_DIR.rglob("*.json"))
    print(f"Found {len(files)} match files\n")

    patched = 0
    for path in files:
        try:
            if patch_file(path):
                patched += 1
                print(f"Patched: {path}")
        except Exception as e:
            print(f"Error patching {path}: {e}")

    print(f"\nDone. {patched} files patched out of {len(files)} total.")


if __name__ == "__main__":
    main()
