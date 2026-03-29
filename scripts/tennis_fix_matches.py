import json
from pathlib import Path

print("FIXING TENNIS MATCHES")

MATCH_DIR = Path("docs/data/tennis/matches")
MATCH_DIR.mkdir(parents=True, exist_ok=True)

years = [2025, 2026]

fixed_count = 0
skipped = 0

for year in years:
    path = MATCH_DIR / f"{year}.json"

    if not path.exists():
        print(f"⚠️ Missing file: {path}")
        skipped += 1
        continue

    try:
        data = json.loads(path.read_text())
    except Exception as e:
        print(f"❌ Bad JSON: {path} ({e})")
        skipped += 1
        continue

    matches = data.get("matches")

    # ✅ FIX: allow empty lists (this was your issue)
    if matches is None:
        print(f"⚠️ No matches key in {path}")
        skipped += 1
        continue

    if not isinstance(matches, list):
        print(f"⚠️ Invalid structure in {path}")
        skipped += 1
        continue

    if len(matches) == 0:
        print(f"⚠️ No matches yet in {year} (this is fine)")
        continue

    fixed_matches = []

    for m in matches:
        if not isinstance(m, dict):
            continue

        fixed = {
            "tournament": m.get("tournament"),
            "round": m.get("round"),
            "date": m.get("date"),
            "player1": m.get("player1"),
            "player2": m.get("player2"),
            "score": m.get("score")
        }

        if not fixed["player1"] or not fixed["player2"]:
            continue

        fixed_matches.append(fixed)

    path.write_text(json.dumps({
        "season": year,
        "matches": fixed_matches
    }, indent=2))

    print(f"✅ Fixed {year} ({len(fixed_matches)} matches)")
    fixed_count += 1

print("\nDONE")
print(f"Fixed: {fixed_count}")
print(f"Skipped: {skipped}")
