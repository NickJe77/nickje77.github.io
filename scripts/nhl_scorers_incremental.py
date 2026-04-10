name: NHL Scorers All Seasons

on:
  workflow_dispatch:
  schedule:
    - cron: "0 6 * * *"

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - run: pip install requests

      - run: mkdir -p docs/data/nhl/boxscores

      - run: python scripts/nhl_scorers_all.py

      - run: |
          git config user.name "github-actions"
          git config user.email "actions@github.com"
          git add docs/data/nhl/boxscores
          git commit -m "Update NHL scorers all seasons" || echo "No changes"
          git push
