"""Stage 4: analyze constant-velocity TMW bracketing welds.

Use TMCA V_NC as the starting estimate, then perform several TMW welds at
constant V_step values until no-crack and full-crack endpoints are bracketed.
"""

# Batch scripts save figures to files and should not open GUI windows.
# The manual picker script (09_pick_weld_start.py) intentionally does NOT use Agg.
import matplotlib
matplotlib.use("Agg")
from pathlib import Path
import argparse
from _bootstrap import bootstrap
ROOT = bootstrap(__file__)
from tmw_tmca_analysis.workflow import analyze_tmw_bracketing

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Analyze individual TMW bracketing runs.")
    p.add_argument("--manifest", type=Path, default=ROOT / "data" / "manifest" / "tmw_bracketing_manifest_template.csv")
    p.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "04_tmw_run_analysis")
    p.add_argument("--config", type=Path, default=ROOT / "config" / "default_analysis_config.json")
    args = p.parse_args()
    out = analyze_tmw_bracketing(ROOT, args.manifest, args.output_dir, config_path=args.config)
    print(f"Analyzed {len(out)} TMW runs.")
    print(f"Check the per-run plots: {args.output_dir / 'run_plots'}")
    print(f"Run metrics: {args.output_dir / 'tmw_run_metrics.csv'}")
    print("Next: python scripts/05_fit_tmw_conditions.py")
