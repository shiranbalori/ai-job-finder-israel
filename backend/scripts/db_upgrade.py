#!/usr/bin/env python3
"""
Apply Alembic migrations to PostgreSQL / Supabase.

Prefer: python scripts/db_init.py

This script is an alias kept for compatibility with docs and CI.
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from scripts.db_init import main

if __name__ == "__main__":
    sys.exit(main())
