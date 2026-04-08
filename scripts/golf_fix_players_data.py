import json
import re

FILE = "docs/data/golf/pga_winners.json"


def clean(name):
    if not name:
        return ""

    name = str(name)

    # remove weird spaces
    name = name.replace("\xa0", " ")

    # remove brackets
    name = re.sub(r"\s*\(.*?\)", "", name)

    # remove junk
    name = name.replace("*", "").strip()

    # split combo names (keep first only)
    for sep in [" / ", "/", " & ", "&", " and ", " And "]:
        if sep in name:
            name = name.split(sep)[0]

    # normalize spacing
    name = re.sub(r"\s+", " ", name).strip()

    if name.lower() in ["not played", "-", "—", ""]:
        return ""

    # 🔥 PROPER CASE
    name = " ".join([w.capitalize() for w in name.lower().split()])

    # 🔥 FIX KNOWN EDGE CASES
    fixes = {
        "Rory Mcilroy": "Rory McIlroy",
        "Mac O Grady": "Mac O'Grady",
        "O Meara": "O'Meara"
    }

    return fixes.get(name, name)


def main():
    with open(FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    cleaned_data = []
    changed = 0

    for row in data:
        old = row.get("winner", "")
        new = clean(old)

        if old != new:
            row["winner"] = new
            changed += 1

        cleaned_data.append(row)

    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(cleaned_data, f, indent=2)

    print(f"Cleaned {changed} player names")


if __name__ == "__main__":
    main()
