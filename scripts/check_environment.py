"""Check that the Python environment can run the TMW/TMCA workflow.

Run this first on a new computer:

    python scripts/check_environment.py

If an import fails, install the dependencies with:

    python -m pip install -r requirements.txt
"""
from _bootstrap import bootstrap
ROOT = bootstrap(__file__)
import sys
import importlib


if __name__ == "__main__":
    print(f"Python: {sys.version.split()[0]}")
    print(f"Repository root: {ROOT}")
    for name in ["numpy", "pandas", "matplotlib"]:
        module = importlib.import_module(name)
        print(f"{name}: {getattr(module, '__version__', 'installed')}")
    print("Environment check passed.")
