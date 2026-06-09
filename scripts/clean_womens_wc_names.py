#!/usr/bin/env python3
"""
clean_womens_wc_names.py

Strips country code prefixes/suffixes from team names in Women's WC seasons JSON files.
e.g. "China PR cn" -> "China PR", "no Norway" -> "Norway", "us USA" -> "United States"

Run from the root of your GitHub repo:
  python scripts/clean_womens_wc_names.py
"""

import json
import re
import sys
from pathlib import Path

REPO_ROOT   = Path(__file__).parent.parent
SEASONS_DIR = REPO_ROOT / "docs" / "data" / "women's-wc" / "womens-world-cup" / "seasons"

ISO_CODES = {
    "ar","au","at","be","br","cm","ca","cl","cn","co","cr","dk",
    "en","eng","es","fi","fr","de","gh","ht","ie","it","jm","jp",
    "ma","nl","nz","ng","no","pa","ph","pt","kr","za","ko","se",
    "ch","tz","us","vn","zm","gb","tw","nk","gq",
}

# After stripping code, apply these normalisations
NORMALISATIONS = {
    "USA":               "United States",
    "Korea Republic":    "South Korea",
    "Republic of Korea": "South Korea",
    "Chinese Taipei":    "Chinese Taipei",
}

def clean_name(name: str) -> str:
    if not name:
        return name
    name = name.strip()
    parts = name.split()

    # Trailing code: "China PR cn" -> "China PR"
    if len(parts) >= 2 and parts[-1].lower() in ISO_CODES:
        name = " ".join(parts[:-1]).strip()
    # Leading code: "no Norway" -> "Norway"
    elif len(parts) >= 2 and parts[0].lower() in ISO_CODES:
        name = " ".join(parts[1:]).strip()

    return NORMALISATIONS.get(name, name)

def clean_venue(venue: str) -> str:
    if not venue:
        return venue
    return venue.replace(" (Neutral Site)", "").strip()

def clean_game(game: dict) -> dict:
    if "home" in game:
        game["home"] = clean_name(game["home"])
    if "away" in game:
        game["away"] = clean_name(game["away"])
    if "venue" in game:
        game["venue"] = clean_venue(game["venue"])
    return game

def main():
    if not SEASONS_DIR.exists():
        print(f"❌  Seasons directory not found: {SEASONS_DIR}", file=sys.stderr)
        sys.exit(1)

    files = sorted(SEASONS_DIR.glob("*.json"))
    print(f"📂  Found {len(files)} season files\n")

    changed = 0
    for fp in files:
        try:
            with open(fp, encoding="utf-8") as f:
                original = f.read()
                data = json.loads(original)
        except Exception as e:
            print(f"⚠️  Skipping {fp}: {e}")
            continue

        games = data.get("games", data) if isinstance(data, dict) else data
        for game in games:
            clean_game(game)

        new_content = json.dumps(data, indent=2, ensure_ascii=False)
        if new_content != original:
            with open(fp, "w", encoding="utf-8") as f:
                f.write(new_content)
            changed += 1
            print(f"  ✅ {fp.name}")

    print(f"\n🏆  Cleaned {changed} of {len(files)} files")
    print("Now re-run build_womens_wc_data.py to regenerate players/teams/team-stats JSON.")

if __name__ == "__main__":
    main()
