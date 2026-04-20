import json
import os

BASE = "docs/data/tennis"
OUT = os.path.join(BASE, "full_match_database.json")

def main():

    matches = []

    # Sample real structure (this is what your site expects)
    for i in range(1, 51):
        matches.append({
            "date": f"2025-01-{str(i%28+1).zfill(2)}",
            "tournament": "Australian Open",
            "player1": f"Player {i}",
            "player2": f"Player {i+1}",
            "score": "6-4 6-3"
        })

    os.makedirs(BASE, exist_ok=True)

    with open(OUT, "w") as f:
        json.dump(matches, f, indent=2)

    print("✅ MATCH DATA CREATED:", len(matches))


if __name__ == "__main__":
    main()
