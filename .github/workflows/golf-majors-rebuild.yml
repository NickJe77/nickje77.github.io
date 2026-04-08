name: Golf Majors Full Rebuild

on:
  workflow_dispatch:

jobs:
  rebuild:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repo
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install requests beautifulsoup4

      - name: Run majors rebuild
        run: |
          python scripts/golf_full_rebuild_majors.py

      - name: Commit updated data
        run: |
          git config user.name "github-actions"
          git config user.email "actions@github.com"
          git add docs/data/golf/pga_winners.json
          git commit -m "Full rebuild golf majors (clean + complete)" || echo "No changes"
          git push
