"""Convert raw controller XML files to standardized control CSV files.

Example:
    python scripts/07_convert_raw_xml_folder.py --input-dir raw_data/TMCA --output-dir data/control_csv/tmca_raw
    python scripts/07_convert_raw_xml_folder.py --input-dir raw_data/TMW  --output-dir data/control_csv/tmw_raw
"""
from pathlib import Path
import argparse
from _bootstrap import bootstrap
ROOT = bootstrap(__file__)
from tmw_tmca_analysis.raw_import import convert_xml_folder

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Convert raw TMW/TMCA controller XML files to standardized control CSV files.")
    p.add_argument("--input-dir", type=Path, required=True, help="Folder containing raw XML controller logs. Subfolders are scanned recursively.")
    p.add_argument("--output-dir", type=Path, required=True, help="Folder where standardized control CSV files will be written.")
    args = p.parse_args()
    inv = convert_xml_folder(args.input_dir, args.output_dir)
    print(f"Scanned XML files under: {args.input_dir}")
    print(f"Converted: {(inv['status'] == 'converted').sum()} file(s)")
    print(f"Failed/skipped failures: {(inv['status'] == 'failed').sum()} file(s)")
    print(f"Inventory: {args.output_dir / 'conversion_inventory.csv'}")
