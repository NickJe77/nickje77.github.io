import json
from pathlib import Path

MATCH_DIR = Path("docs/data/tennis/matches")
OUT_FILE = Path("docs/data/tennis/history.json")

all_matches = []

# -------------------------
# LOAD ALL YEARS
# -------------------------
for file in sorted(MATCH_DIR.glob("*.json")):

    print("Loading:", file.name)

    try:
        data = json.loads(file.read_text())
        if isinstance(data, list):
            all_matches.extend(data)
    except Exception as e:
        print("ERROR:", file.name, e)

# -------------------------
# VALIDATE + CLEAN
# -------------------------
clean = []

for m in all_matches:

    if not m.get("tournament"):
        continue
    if not m.get("player1") or not m.get("player2"):
        continue

    clean.append(m)

# -------------------------
# SORT
# -------------------------
clean.sort(key=lambda x: (
    x.get("date",""),
    x.get("tournament","")
))

# -------------------------
# SAVE
# -------------------------
OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
OUT_FILE.write_text(json.dumps(clean, indent=2))

print(f"✅ DONE: {len(clean)} matches saved")
