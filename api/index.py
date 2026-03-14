"""Vercel serverless entry point.

This file re-exports the FastAPI ``app`` instance so that Vercel's
@vercel/python runtime can discover it automatically.
"""

import sys
from pathlib import Path

# Add the `src` directory to sys.path so that `app.*` package imports work.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from app.main import app  # noqa: E402, F401
