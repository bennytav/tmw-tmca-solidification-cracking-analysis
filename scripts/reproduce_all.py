
# Batch scripts save figures to files and should not open GUI windows.
# The manual picker script (09_pick_weld_start.py) intentionally does NOT use Agg.
import matplotlib
matplotlib.use("Agg")
"""Reproduce the manuscript summary figures from processed data."""
from pathlib import Path
import argparse
from _bootstrap import bootstrap
ROOT = bootstrap(__file__)
from tmw_tmca_analysis.workflow import reproduce_manuscript

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Reproduce manuscript summary figures from processed CSV files.")
    p.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "manuscript_reproduction")
    args = p.parse_args()
    reproduce_manuscript(ROOT, args.output_dir)
    print(f"Manuscript reproduction outputs: {args.output_dir}")
