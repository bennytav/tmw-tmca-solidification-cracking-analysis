
# Batch scripts save figures to files and should not open GUI windows.
# The manual picker script (09_pick_weld_start.py) intentionally does NOT use Agg.
import matplotlib
matplotlib.use("Agg")
"""Stage 2: summarize TMCA V_NC results after run-level plots are checked."""
from pathlib import Path
import argparse
from _bootstrap import bootstrap
ROOT = bootstrap(__file__)
from tmw_tmca_analysis.workflow import summarize_tmca_screening

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Summarize TMCA V_NC results and plot screening summary.")
    p.add_argument("--metrics", type=Path, default=ROOT / "outputs" / "01_tmca_run_analysis" / "tmca_run_metrics.csv")
    p.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "02_tmca_screening_summary")
    p.add_argument("--config", type=Path, default=ROOT / "config" / "default_analysis_config.json")
    args = p.parse_args()
    summary = summarize_tmca_screening(args.metrics, args.output_dir, config_path=args.config)
    print(f"Summarized {len(summary)} TMCA condition groups.")
    print(f"Summary table: {args.output_dir / 'tmca_screening_summary.csv'}")
    print(f"Figure: {args.output_dir / 'TMCA_transition_range_TMWstyle_box.png'}")
    print(f"Initial TMW plan: {args.output_dir / 'recommended_tmw_vstep_plan.csv'}")
    print("Next: python scripts/03_plan_tmw_from_tmca.py")
