
# Batch scripts save figures to files and should not open GUI windows.
# The manual picker script (09_pick_weld_start.py) intentionally does NOT use Agg.
import matplotlib
matplotlib.use("Agg")
"""Stage 3: write an initial TMW V_step plan from TMCA V_NC results."""
from pathlib import Path
import argparse
from _bootstrap import bootstrap
ROOT = bootstrap(__file__)
from tmw_tmca_analysis.workflow import plan_tmw_from_tmca

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Create/recreate a TMW V_step plan from TMCA screening summary.")
    p.add_argument("--tmca-summary", type=Path, default=ROOT / "outputs" / "02_tmca_screening_summary" / "tmca_screening_summary.csv")
    p.add_argument("--output-csv", type=Path, default=ROOT / "outputs" / "03_tmw_vstep_plan" / "recommended_tmw_vstep_plan.csv")
    args = p.parse_args()
    plan = plan_tmw_from_tmca(args.tmca_summary, args.output_csv)
    print(f"Wrote {len(plan)} suggested V_step entries: {args.output_csv}")
    print("Use this as a starting plan only; add lower/higher V_step levels until no-crack and full-crack endpoints are bracketed.")
