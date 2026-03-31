from pathlib import Path

print("ADDING ANALYTICS TO ALL HTML FILES")

ROOT = Path("docs")

SNIPPET = """<script src="/js/analytics.js"></script>"""

count = 0

for file in ROOT.rglob("*.html"):
    text = file.read_text(encoding="utf-8")

    # skip if already added
    if SNIPPET in text:
        continue

    # insert right after <head>
    if "<head>" in text:
        text = text.replace("<head>", "<head>\n  " + SNIPPET, 1)
        file.write_text(text, encoding="utf-8")
        count += 1
        print(f"Updated: {file}")

print(f"\nDONE — updated {count} files")
