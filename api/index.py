"""Vercel serverless entry point.

This file re-exports the FastAPI ``app`` instance so that Vercel's
@vercel/python runtime can discover it automatically.
"""

import sys
from pathlib import Path

# api/index.py -> parent = api/ -> parent.parent = project root
# We need <project_root>/src on sys.path so `app.*` imports work.
_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root / "src"))

from app.main import app  # noqa: E402, F401
