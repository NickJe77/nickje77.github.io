import os
import json

folder = "docs/data/baseball/boxscores/2026"

files = []

if os.path.exists(folder):
for f in os.listdir(folder):
if f.endswith(".json") and f != "index.json":
files.append(f)

files.sort()

output_path = os.path.join(folder, "index.json")

with open(output_path, "w") as out:
json.dump(files, out, indent=2)

print(f"Index built: {len(files)} files")
