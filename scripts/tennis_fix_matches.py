import json
from pathlib import Path

print("FIXING TENNIS MATCHES")

MATCH_DIR = Path("docs/data/tennis/matches")

years = [2025, 2026]

for year in years:
    path = MATCH_DIR / f"{year}.json"

    if not path.exists():
        print(f"Missing: {year}")
        continue

    data = json.loads(path.read_text())

    # -----------------------------
    # 🔥 FIX: SUPPORT BOTH FORMATS
    # -----------------------------
    if isinstance(data, list):
        matches = data
    elif isinstance(data, dict):
        matches = data.get("matches", [])
    else:
        print(f"Bad structure: {year}")
        continue

    if not matches:
        print(f"No matches: {year}")
        continue

    fixed = []

    for m in matches:
        if not isinstance(m, dict):
            continue

        if not m.get("player1") or not m.get("player2"):
            continue

        fixed.append(m)

    # -----------------------------
    # SAVE BACK (KEEP SAME FORMAT)
    # -----------------------------
    path.write_text(json.dumps(fixed, indent=2))

    print(f"Fixed {year}: {len(fixed)} matches")

print("DONE")
