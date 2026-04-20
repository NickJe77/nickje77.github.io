import json
import os

OUT = "docs/data/tennis/seasons"

def save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def build(year):
    return [
        {
            "tournament": "Australian Open",
            "surface": "Hard",
            "location": "Melbourne",
            "tour": "ATP",
            "start_date": f"{year}-01-15",
            "end_date": f"{year}-01-28",
            "date": f"{year}-01-15"
        },
        {
            "tournament": "Acapulco",
            "surface": "Hard",
            "location": "Acapulco",
            "tour": "ATP",
            "start_date": f"{year}-02-24",
            "end_date": f"{year}-03-02",
            "date": f"{year}-02-24"
        },
        {
            "tournament": "Adelaide",
            "surface": "Hard",
            "location": "Adelaide",
            "tour": "ATP",
            "start_date": f"{year}-01-01",
            "end_date": f"{year}-01-07",
            "date": f"{year}-01-01"
        }
    ]

def main():
    save(f"{OUT}/2025.json", build("2025"))
    save(f"{OUT}/2026.json", build("2026"))
    print("✅ TEST DATA WRITTEN")

if __name__ == "__main__":
    main()
