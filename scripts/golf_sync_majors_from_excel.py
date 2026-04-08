name: Sync Majors From Excel (SAFE)

on:
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - run: pip install pandas openpyxl

      - run: python scripts/golf_sync_majors_from_excel.py

      - run: |
          git config user.name "github-actions"
          git config user.email "actions@github.com"
          git add docs/data/golf/pga_winners.json
          git commit -m "Sync majors from Excel (safe)" || echo "No changes"
          git push
