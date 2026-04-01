import json
from pathlib import Path

print("FIX 2026 EVENTS → MATCH 2025 FORMAT (SAFE)")

# -------------------------
# HARD LOCK TO 2026 ONLY
# -------------------------
BOX_DIR = Path("docs/data/baseball/boxscores/2026")

if "2026" not in str(BOX_DIR):
    print("SAFETY STOP")
    exit()

# -------------------------
# PLAYER MAP (ID → SHORT ID)
# -------------------------
PLAYER_MAP_FILE = Path("docs/data/baseball/players.json")

player_map = {}

if PLAYER_MAP_FILE.exists():
    try:
        with open(PLAYER_MAP_FILE) as f:
            data = json.load(f)
            for p in data:
                pid = str(p.get("player_id", ""))
                sid = p.get("short_id") or pid
                player_map[pid] = sid
        print(f"Loaded player map: {len(player_map)} players")
    except:
        print("Failed to load player map")

# -------------------------
# EVENT CONVERTER
# -------------------------
def convert(desc):

    d = str(desc).lower()

    # STRIKEOUT
    if "strikeout" in d or "strikes out" in d or "struck out" in d:
        return ["02", "CF.FS", "K"]

    # GROUND OUT
    if "grounds out" in d or "grounded out" in d:
        return ["00", "X", "63"]

    # FLY OUT
    if "flies out" in d or "flied out" in d:
        return ["00", "X", "8/F8"]

    # POP OUT
    if "pops out" in d or "popped out" in d:
        return ["00", "X", "2/P"]

    # LINE OUT
    if "lines out" in d or "lined out" in d:
        return ["00", "X", "L"]

    # DOUBLE PLAY
    if "double play" in d:
        return ["00", "X", "DP"]

    # SINGLE
    if "single" in d:
        return ["11", "CBX", "S"]

    # DOUBLE
    if "double" in d:
        return ["20", "CBX", "D"]

    # TRIPLE
    if "triple" in d:
        return ["30", "CBX", "T"]

    # HOME RUN
    if "home run" in d or "homers" in d:
        return ["40", "CBX", "HR"]

    # WALK
    if "walk" in d:
        return ["14", "BB", "W"]

    # DEFAULT
    return ["00", "X", "UNK"]

# -------------------------
# PROCESS FILES
# -------------------------
files = list(BOX_DIR.glob("*.json"))

if not files:
    print("No 2026 files found")
    exit()

print(f"Processing {len(files)} files")

for file in files:

    try:
        with open(file) as f:
            data = json.load(f)

        new_events = []

        for e in data.get("events", []):

            # -------------------------
            # REMOVE NON-PLAY ROWS
            # -------------------------
            if not isinstance(e, list):
                continue

            if len(e) < 5:
                continue

            if e[0] != "play":
                continue

            try:
                inning = str(e[1])
                half = str(e[2])
                pid = str(e[3])
                desc = e[4]

                short_id = player_map.get(pid, pid)

                a, b, c = convert(desc)

                new_events.append([
                    "play",
                    inning,
                    half,
                    short_id,
                    a,
                    b,
                    c
                ])

            except:
                continue

        # -------------------------
        # WRITE BACK (ONLY EVENTS)
        # -------------------------
        data["events"] = new_events

        with open(file, "w") as f:
            json.dump(data, f, indent=2)

    except Exception as ex:
        print("Skipped:", file.name)

print("DONE — 2026 NOW MATCHES 2025 FORMAT")
