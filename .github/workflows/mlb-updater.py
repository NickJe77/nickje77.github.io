name: MLB Updater

on:
  workflow_dispatch:
  schedule:
    - cron: "0 6 * * *"

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: 3.11

      - name: Install deps
        run: |
          pip install requests

      - name: Build schedule
        run: |
          python scripts/mlb_schedule.py

      - name: Build boxscores
        run: |
          python scripts/mlb_boxscores.py

      - name: Commit
        run: |
          git config user.name "github-actions"
          git config user.email "actions@github.com"
          git add docs/data/baseball
          git commit -m "MLB update" || echo "No changes"
          git push
