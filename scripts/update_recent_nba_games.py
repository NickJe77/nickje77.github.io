import json
import os

OUTPUT_DIR = "docs/data/nba/2026"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("Testing file output...")

test_game = {
    "game_id": "TEST123",
    "season": 2026,
    "date": "2026-02-16",
    "home_team": "Test Home",
    "away_team": "Test Away",
    "home_score": 100,
    "away_score": 99,
    "arena": "Test Arena",
    "players": []
}

file_path = f"{OUTPUT_DIR}/TEST123.json"

with open(file_path, "w") as f:
    json.dump(test_game, f, indent=2)

print("Saved:", file_path)
