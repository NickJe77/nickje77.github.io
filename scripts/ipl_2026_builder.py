import requests
import zipfile
import io
import json
from pathlib import Path

print("IPL 2026 CRICSHEET BUILDER + PLAYERS")

OUTPUT = Path("docs/data/ipl/ipl_2026_FULL.json")
PLAYERS_FILE = Path("docs/data/ipl/players.json")

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

ZIP_URL = "https://cricsheet.org/downloads/ipl_json.zip"

# -------------------------
# LOAD EXISTING MATCHES
# -------------------------
existing = []
existing_ids = set()

if OUTPUT.exists():
    with open(OUTPUT) as f:
        existing = json.load(f)
        for m in existing:
            if "file" in m:
                existing_ids.add(m["file"])

print("Existing matches:", len(existing))

# -------------------------
# LOAD EXISTING PLAYERS (SAFE)
# -------------------------
players = {}

if PLAYERS_FILE.exists():
    with open(PLAYERS_FILE) as f:
        players = json.load(f)

print("Existing players:", len(players))

# -------------------------
# DOWNLOAD ZIP
# -------------------------
print("Downloading Cricsheet ZIP...")
r = requests.get(ZIP_URL)

if r.status_code != 200:
    print("❌ Failed to download zip")
    exit()

z = zipfile.ZipFile(io.BytesIO(r.content))
files = z.namelist()

print("Files in zip:", len(files))

# -------------------------
# HELPERS
# -------------------------
def slug(name):
    return name.lower().replace(".", "").replace(" ", "-")

# -------------------------
# PROCESS MATCHES
# -------------------------
new_matches = []
new_players_added = 0

for file_name in files:

    if not file_name.endswith(".json"):
        continue

    try:
        raw = z.read(file_name).decode("utf-8")
        data = json.loads(raw)

        info = data.get("info", {})

        season = str(info.get("season", ""))
        event_name = str(info.get("event", {}).get("name", "")).lower()

        # IPL 2026 only
        if "2026" not in season:
            continue

        if "indian premier league" not in event_name:
            continue

        short_name = file_name.split("/")[-1]

        if short_name in existing_ids:
            continue

        # -------------------------
        # ADD MATCH
        # -------------------------
        data["file"] = short_name
        new_matches.append(data)

        print("✔ match added", short_name)

        # -------------------------
        # EXTRACT PLAYERS
        # -------------------------
        player_lists = info.get("players", {})

        for team_players in player_lists.values():
            for p in team_players:

                s = slug(p)

                if s not in players:
                    players[s] = p
                    new_players_added += 1

    except Exception as e:
        print("fail", file_name)

# -------------------------
# MERGE MATCHES
# -------------------------
combined = existing + new_matches

def get_date(m):
    try:
        return m["info"]["dates"][0]
    except:
        return ""

combined.sort(key=get_date)

# -------------------------
# SAVE MATCHES
# -------------------------
with open(OUTPUT, "w") as f:
    json.dump(combined, f, indent=2)

# -------------------------
# SAVE PLAYERS (SAFE)
# -------------------------
with open(PLAYERS_FILE, "w") as f:
    json.dump(players, f, indent=2)

# -------------------------
# DONE
# -------------------------
print("NEW MATCHES:", len(new_matches))
print("TOTAL MATCHES:", len(combined))
print("NEW PLAYERS:", new_players_added)
print("TOTAL PLAYERS:", len(players))
print("DONE")
