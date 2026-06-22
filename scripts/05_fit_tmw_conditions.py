
# Batch scripts save figures to files and should not open GUI windows.
# The manual picker script (09_pick_weld_start.py) intentionally does NOT use Agg.
import matplotlib
matplotlib.use("Agg")
"""Stage 5: fit V_C--V_F for each TMW condition."""
from pathlib import Path
import argparse
from _bootstrap import bootstrap
ROOT = bootstrap(__file__)
from tmw_tmca_analysis.workflow import fit_tmw_conditions

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Fit V_C--V_F transition interval for TMW condition(s).")
    p.add_argument("--metrics", type=Path, default=ROOT / "outputs" / "04_tmw_run_analysis" / "tmw_run_metrics.csv")
    p.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "05_tmw_condition_fits")
    p.add_argument("--condition-id", type=str, default=None, help="Optional condition_id to fit one condition only.")
    p.add_argument("--config", type=Path, default=ROOT / "config" / "default_analysis_config.json")
    args = p.parse_args()
    summary = fit_tmw_conditions(args.metrics, args.output_dir, condition_id=args.condition_id, config_path=args.config)
    print(f"Fitted {len(summary)} TMW condition groups.")
    print(f"Summary table: {args.output_dir / 'tmw_condition_transition_summary.csv'}")
    print(f"Condition plots: {args.output_dir / 'condition_transition_plots'}")
    print("Next: python scripts/06_compare_tmw_conditions.py")
