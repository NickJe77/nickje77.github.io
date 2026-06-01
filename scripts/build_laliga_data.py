#!/usr/bin/env python3
"""
build_laliga_data.py

Reads all match JSON files from docs/data/laliga/matches/<season>/*.json
and generates three output files:
  - docs/data/laliga/players.json
  - docs/data/laliga/teams.json
  - docs/data/laliga/team-stats.json

Place this file in the scripts/ folder.
Run from the root of your GitHub repo (nickje77.github.io/)
"""

import json
import sys
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
REPO_ROOT   = Path(__file__).parent.parent
MATCHES_DIR = REPO_ROOT / "docs" / "data" / "laliga" / "matches"
OUT_DIR     = REPO_ROOT / "docs" / "data" / "laliga"
