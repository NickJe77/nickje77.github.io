import json
import os

OUT = "docs/data/tennis/matches"

def save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def main():

    matches = [
        {
            "tournament": "Australian Open",
            "date": "2025-01-15",
            "player1": "Novak Djokovic",
            "player2": "Carlos Alcaraz",
            "score": "6-4 6-4"
        },
        {
            "tournament": "Australian Open",
            "date": "2025-01-16",
            "player1": "Jannik Sinner",
            "player2": "Daniil Medvedev",
            "score": "7-6 6-3"
        }
    ]

    save(f"{OUT}/2025.json", matches)

    print("✅ Matches created")

if __name__ == "__main__":
    main()
