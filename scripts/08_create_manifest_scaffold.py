"""Create a manifest scaffold from standardized control CSV files.

The scaffold is not the final manifest.  You must fill the missing metadata and
crack measurements before running the TMCA/TMW analysis scripts.
"""
from pathlib import Path
import argparse
from _bootstrap import bootstrap
ROOT = bootstrap(__file__)
from tmw_tmca_analysis.raw_import import make_manifest_scaffold

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Create a TMCA or TMW manifest scaffold from standardized control CSV files.")
    p.add_argument("--control-dir", type=Path, required=True, help="Folder containing standardized control CSV files.")
    p.add_argument("--protocol", choices=["TMCA", "TMW"], required=True, help="Protocol for all rows in this scaffold.")
    p.add_argument("--output-csv", type=Path, required=True, help="Manifest CSV to write.")
    p.add_argument("--metrics-dir", type=Path, default=None, help="Optional folder containing *_metrics.json files to pre-fill some fields.")
    args = p.parse_args()
    df = make_manifest_scaffold(args.control_dir, args.output_csv, protocol=args.protocol, metrics_dir=args.metrics_dir)
    print(f"Wrote {len(df)} manifest row(s): {args.output_csv}")
    print("Open this CSV and fill the missing material, process, timing, and crack-measurement fields before analysis.")
