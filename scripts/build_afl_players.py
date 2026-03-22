import json
from pathlib import Path

print("BUILD AFL PLAYERS — PRESERVE ROUND")

INPUT = Path("docs/data/afl/afl_2026.json")
OUTPUT = Path("docs/data/afl/afl_2026.json")  # overwriting same file

if not INPUT.exists():
    raise Exception("Input file missing")

with open(INPUT) as f:
    data = json.load(f)

players = []

for row in data:

    entry = {
        "player": row.get("player"),
        "played_for": row.get("played_for"),
        "played_against": row.get("played_against"),
        "season": row.get("season"),

        # 🔥 THIS IS THE FIX
        "round": row.get("round"),

        "K": row.get("K", 0),
        "HB": row.get("HB", 0),
        "D": row.get("D", 0),
        "M": row.get("M", 0),
        "G": row.get("G", 0),
        "B": row.get("B", 0),
        "T": row.get("T", 0),
        "HO": row.get("HO", 0),
        "GA": row.get("GA", 0),
        "I50": row.get("I50", 0),
        "CL": row.get("CL", 0),
        "CG": row.get("CG", 0),
        "R50": row.get("R50", 0),
        "FF": row.get("FF", 0),
        "FA": row.get("FA", 0),
        "AF": row.get("AF", 0),
        "SC": row.get("SC", 0)
    }

    players.append(entry)

print("PLAYERS BUILT:", len(players))

with open(OUTPUT, "w") as f:
    json.dump(players, f, indent=2)

print("DONE — ROUND PRESERVED")
