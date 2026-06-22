"""Stage 1: analyze single-run TMCA screening welds.

Before running:
1. Perform TMCA welds for fast screening.
2. Export one control CSV per weld.
3. Fill one manifest row per weld.
4. Measure the surface crack end L_surf, or enter L_CT if CT is used.
"""

# Batch scripts save figures to files and should not open GUI windows.
# The manual picker script (09_pick_weld_start.py) intentionally does NOT use Agg.
import matplotlib
matplotlib.use("Agg")
from pathlib import Path
import argparse
from _bootstrap import bootstrap
ROOT = bootstrap(__file__)
from tmw_tmca_analysis.workflow import analyze_tmca_screening

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Analyze individual TMCA screening runs.")
    p.add_argument("--manifest", type=Path, default=ROOT / "data" / "manifest" / "tmca_screening_manifest_template.csv")
    p.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "01_tmca_run_analysis")
    p.add_argument("--config", type=Path, default=ROOT / "config" / "default_analysis_config.json")
    args = p.parse_args()
    out = analyze_tmca_screening(ROOT, args.manifest, args.output_dir, config_path=args.config)
    print(f"Analyzed {len(out)} TMCA runs.")
    print(f"Check the per-run plots: {args.output_dir / 'run_plots'}")
    print(f"Run metrics: {args.output_dir / 'tmca_run_metrics.csv'}")
    print("Next: python scripts/02_summarize_tmca_screening.py")
