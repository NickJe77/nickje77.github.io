name: World Cup Builder

on:
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install deps
        run: |
          pip install requests beautifulsoup4

      - name: Run scraper
        run: |
          python scripts/world_cup_builder.py

      - name: Commit & Push
        run: |
          git config user.name "github-actions"
          git config user.email "actions@github.com"
          git add docs/data/cricket/
          git commit -m "Update World Cup data" || echo "No changes"
          git push
