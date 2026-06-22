
# Batch scripts save figures to files and should not open GUI windows.
# The manual picker script (09_pick_weld_start.py) intentionally does NOT use Agg.
import matplotlib
matplotlib.use("Agg")
"""Stage 6: compare fitted TMW V_C--V_F intervals across conditions."""
from pathlib import Path
import argparse
from _bootstrap import bootstrap
ROOT = bootstrap(__file__)
from tmw_tmca_analysis.workflow import compare_tmw_conditions

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Compare fitted V_C--V_F transition intervals across TMW conditions.")
    p.add_argument("--transition-summary", type=Path, default=ROOT / "outputs" / "05_tmw_condition_fits" / "tmw_condition_transition_summary.csv")
    p.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "06_tmw_condition_comparison")
    p.add_argument("--config", type=Path, default=ROOT / "config" / "default_analysis_config.json")
    args = p.parse_args()
    summary = compare_tmw_conditions(args.transition_summary, args.output_dir, config_path=args.config)
    print(f"Compared {len(summary)} TMW condition groups.")
    print(f"Comparison figure: {args.output_dir / 'Transition_ranges_summary.png'}")
