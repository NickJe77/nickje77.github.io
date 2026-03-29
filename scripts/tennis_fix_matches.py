import json
from pathlib import Path

print("FIXING TENNIS MATCHES")

BASE_DIR = Path("docs/data/tennis")
MATCH_DIR = BASE_DIR / "matches"

# Ensure folder exists
MATCH_DIR.mkdir(parents=True, exist_ok=True)

years = [2025, 2026]

fixed_count = 0
skipped = 0

for year in years:
    path = MATCH_DIR / f"{year}.json"

    # -----------------------------
    # FILE DOES NOT EXIST → SKIP
    # -----------------------------
    if not path.exists():
        print(f"⚠️ Missing file: {path} — skipping")
        skipped += 1
        continue

    try:
        data = json.loads(path.read_text())
    except Exception as e:
        print(f"❌ Broken JSON in {path}: {e}")
        skipped += 1
        continue

    # -----------------------------
    # NORMALISE STRUCTURE
    # -----------------------------
    matches = data.get("matches") or data.get("games") or data

    if not isinstance(matches, list):
        print(f"⚠️ Invalid structure in {path}")
        skipped += 1
        continue

    fixed_matches = []

    for m in matches:
        if not isinstance(m, dict):
            continue

        fixed = {}

        # --- NORMALISE FIELDS ---
        fixed["tournament"] = m.get("tournament") or m.get("event")
        fixed["round"] = m.get("round")
        fixed["date"] = m.get("date")

        fixed["player1"] = m.get("player1") or m.get("winner")
        fixed["player2"] = m.get("player2") or m.get("loser")

        fixed["score"] = m.get("score")

        # Skip garbage rows
        if not fixed["player1"] or not fixed["player2"]:
            continue

        fixed_matches.append(fixed)

    # -----------------------------
    # SAVE BACK
    # -----------------------------
    output = {
        "season": year,
        "matches": fixed_matches
    }

    path.write_text(json.dumps(output, indent=2))

    print(f"✅ Fixed {year} — {len(fixed_matches)} matches")
    fixed_count += 1

print("\nDONE")
print(f"Fixed: {fixed_count}")
print(f"Skipped: {skipped}")
