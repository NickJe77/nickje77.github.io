# ---------- WRITE ----------
print("Writing player files...")

# wipe old files
for f in OUT.glob("*.json"):
    f.unlink()

# WRITE PLAYER FILES
for k,v in players.items():
    (OUT / f"{k}.json").write_text(json.dumps(v,indent=2))

# 🔥 FIX: BUILD UNIQUE INDEX
index_map = {}

for k,v in players.items():
    if k not in index_map:
        index_map[k] = {
            "name": v["name"],
            "slug": k
        }

# convert to list
index = list(index_map.values())

# sort
index = sorted(index, key=lambda x: x["name"])

# write
(OUT / "index.json").write_text(json.dumps(index,indent=2))

print("DONE:", len(index))
