#!/usr/bin/env python3
import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT   = Path(os.environ.get("GITHUB_WORKSPACE", str(Path(__file__).parent.parent)))
MATCHES_DIR = REPO_ROOT / "docs" / "data" / "ucl" / "matches"
OUT_DIR     = REPO_ROOT / "docs" / "data" / "ucl"

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

def normalise_team(name: str) -> str:
    name = (name or "").strip()
    return TEAM_NAME_MAP.get(name, name)


def collect_json_files(directory: Path) -> list:
    if not directory.exists():
        print(f"❌  Matches directory not found: {directory}", file=sys.stderr)
        sys.exit(1)
    return sorted(directory.rglob("*.json"))


def season_from_path(file_path: Path) -> str:
    parts = file_path.parts
    try:
        idx = list(parts).index("matches")
        raw = parts[idx + 1]
        m = re.match(r'^(\d{4})-\d*(\d{2})$', raw)
        if m:
            raw = f"{m.group(1)}-{m.group(2)}"
        return raw
    except (ValueError, IndexError):
        return "unknown"


def resolve_team(raw_team: str, player_name: str, home_team: str, away_team: str, known_teams: dict) -> str:
    """Resolve a player's team —
