#!/usr/bin/env python3
"""
clean_womens_wc_names.py

Strips country code suffixes from team names in all Women's WC match JSON files.
e.g. "New Zealand nz" -> "New Zealand", "no Norway" -> "Norway"

Run from the root of your GitHub repo:
  python scripts/clean_womens_wc_names.py
"""

import json
import re
import sys
from pathlib import Path

REPO_ROOT   = Path(__file__).parent.parent
MATCHES_DIR = REPO_ROOT / "docs" / "data" / "women's-wc" / "womens-world-cup" / "matches"

# Two-letter ISO codes that appear as prefixes or suffixes
ISO_CODES = {
    "ar","au","at","be","br","cm","ca","cl","cn","co","cr","dk",
    "en","eng","es","fi","fr","de","gh","ht","ie","it","jm","jp",
    "ma","nl","nz","ng","no","pa","ph","pt","kr","za","ko","se",
    "ch","tz","us","vn","zm","gb","us",
}

def clean_name(name: str) -> str:
    if not name:
        return name
    name = name.strip()

    # Remove trailing code: "New Zealand nz" -> "New Zealand"
    parts = name.split()
    if len(parts) >= 2 and parts[-1].lower() in ISO_CODES:
        name = " ".join(parts[:-1])
        return name.strip()

    # Remove leading code: "no Norway" -> "Norway"
    if len(parts) >= 2 and parts[0].lower() in ISO_CODES:
        name = " ".join(parts[1:])
        return name.strip()

    return name

# Known name normalisations after code stripping
NORMALISATIONS = {
    "Korea Republic": "South Korea",
    "Republic of Korea": "South Korea",
    "United States": "United States",
    "Usa": "United States",
    "USA": "United States",
    "Côte d'Ivoire": "Ivory Coast",
    "England": "England",
}

def normalise(name: str) -> str:
    cleaned = clean_name(name)
    return NORMALISATIONS.get(cleaned, cleaned)

def clean_event_list(events):
    if not events:
        return events
    for e in events:
        if "team" in e:
            e["team"] = normalise(e["team"])
    return events

def clean_match(match: dict) -> dict:
    for key in ("home_team", "away_team"):
        if key in match:
            match[key] = normalise(match[key])
    match["scorers"]      = clean_event_list(match.get("scorers") or [])
    match["yellow_cards"] = clean_event_list(match.get("yellow_cards") or [])
    match["red_cards"]    = clean_event_list(match.get("red_cards") or [])
    return match

def main():
    if not MATCHES_DIR.exists():
        print(f"❌  Matches directory not found: {MATCHES_DIR}", file=sys.stderr)
        sys.exit(1)

    files = sorted(MATCHES_DIR.rglob("*.json"))
    print(f"📂  Found {len(files)} match files\n")

    changed = 0
    for fp in files:
        try:
            with open(fp, encoding="utf-8") as f:
                original = f.read()
                match = json.loads(original)
        except Exception as e:
            print(f"⚠️  Skipping {fp}: {e}")
            continue

        cleaned = clean_match(match)
        new_content = json.dumps(cleaned, indent=2, ensure_ascii=False)

        if new_content != original:
            with open(fp, "w", encoding="utf-8") as f:
                f.write(new_content)
            changed += 1

    print(f"✅  Cleaned {changed} of {len(files)} files")
    print("\nNow re-run build_womens_wc_data.py to regenerate players/teams/team-stats JSON.")

if __name__ == "__main__":
    main()
