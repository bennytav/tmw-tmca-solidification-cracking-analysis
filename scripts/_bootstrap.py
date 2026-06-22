"""Small helper that lets the scripts run without package installation.

The source code lives in ``src/tmw_tmca_analysis``.  When a user runs a script
with:

    python scripts/01_analyze_tmca_screening.py

Python normally searches only the ``scripts`` folder and the global environment.
This helper adds the repository ``src`` folder to ``sys.path`` so imports such
as ``from tmw_tmca_analysis.workflow import ...`` work on a fresh computer.

Users who prefer a standard package installation can instead run:

    python -m pip install -e .
"""
from pathlib import Path
import sys

# Repository root = parent folder of ``scripts``.
REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"

# Put ``src`` at the beginning of the Python search path.
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def bootstrap(_script_file: str | None = None) -> Path:
    """Return the repository root after ensuring ``src`` is importable."""
    return REPO_ROOT


def repo_root() -> Path:
    """Return the repository root path."""
    return REPO_ROOT
