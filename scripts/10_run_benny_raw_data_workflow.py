"""Run the included Benny Tavlovich raw-data workflow.

This script is for the raw data distributed with the repository.  It does the
same work that a new user would do manually:

1. convert the raw controller XML files listed in the prefilled manifests into
   standardized controller CSV files;
2. analyze every TMCA run and save one plot per run;
3. summarize the TMCA screening result;
4. analyze every TMW run and save one plot per run;
5. fit V_C--V_F for each TMW condition; and
6. compare the fitted TMW conditions.

The script does not edit the raw data.  It writes generated CSV files and plots
to ``data/control_csv/`` and ``outputs/benny_raw_data/``.

Typical use:
    python scripts/10_run_benny_raw_data_workflow.py

Useful options:
    python scripts/10_run_benny_raw_data_workflow.py --convert skip
    python scripts/10_run_benny_raw_data_workflow.py --limit-per-protocol 3

``--limit-per-protocol`` is only for quick testing.  Do not use it for the final
reproduction check.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

from _bootstrap import bootstrap
ROOT = bootstrap(__file__)

import pandas as pd

from tmw_tmca_analysis.raw_import import controller_xml_to_standard_csv
from tmw_tmca_analysis.data_io import write_csv
from tmw_tmca_analysis.workflow import (
    analyze_tmca_screening,
    summarize_tmca_screening,
    plan_tmw_from_tmca,
    analyze_tmw_bracketing,
    fit_tmw_conditions,
    compare_tmw_conditions,
)


def _read_manifest(path: Path, limit: int | None = None) -> pd.DataFrame:
    """Read one manifest and optionally keep only the first N rows."""
    df = pd.read_csv(path)
    if limit is not None:
        df = df.head(int(limit)).copy()
    return df


def _convert_rows(df: pd.DataFrame, *, repo_root: Path, skip_existing: bool = True) -> tuple[int, int]:
    """Convert the raw XML files referenced in one manifest.

    Parameters
    ----------
    df:
        Manifest rows containing ``raw_xml`` and ``control_csv`` columns.
    repo_root:
        Repository folder.
    skip_existing:
        If ``True``, do not re-convert files whose standardized CSV already
        exists.  Delete ``data/control_csv`` if you want a completely fresh
        conversion.

    Returns
    -------
    converted, skipped:
        Number of files converted and skipped.
    """
    converted = 0
    skipped = 0
    for _, row in df.iterrows():
        raw_xml = repo_root / str(row["raw_xml"])
        control_csv = repo_root / str(row["control_csv"])

        if not raw_xml.exists():
            raise FileNotFoundError(f"Raw XML listed in manifest was not found: {raw_xml}")

        if skip_existing and control_csv.exists():
            skipped += 1
            continue

        control_csv.parent.mkdir(parents=True, exist_ok=True)
        control = controller_xml_to_standard_csv(raw_xml)
        write_csv(control, control_csv)
        converted += 1
        print(f"converted: {raw_xml.relative_to(repo_root)} -> {control_csv.relative_to(repo_root)}")
    return converted, skipped


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the included raw-data workflow.")
    parser.add_argument(
        "--tmca-manifest",
        type=Path,
        default=ROOT / "data" / "manifest" / "benny_tmca_manifest_prefilled.csv",
        help="Prefilled TMCA manifest to use.",
    )
    parser.add_argument(
        "--tmw-manifest",
        type=Path,
        default=ROOT / "data" / "manifest" / "benny_tmw_manifest_prefilled.csv",
        help="Prefilled TMW manifest to use.",
    )
    parser.add_argument(
        "--convert",
        choices=["needed", "skip"],
        default="needed",
        help="'needed' converts raw XML files if the standardized CSV does not already exist. 'skip' assumes CSV files already exist.",
    )
    parser.add_argument(
        "--limit-per-protocol",
        type=int,
        default=None,
        help="Quick-test option: analyze only the first N TMCA rows and first N TMW rows. Do not use for final reproduction.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config" / "default_analysis_config.json",
        help="Analysis configuration JSON.",
    )
    args = parser.parse_args()

    tmca_manifest = _read_manifest(args.tmca_manifest, args.limit_per_protocol)
    tmw_manifest = _read_manifest(args.tmw_manifest, args.limit_per_protocol)

    # If the user selected a small limit, write temporary manifests so the
    # downstream workflow scripts only analyze the selected rows.
    work_dir = ROOT / "outputs" / "benny_raw_data" / "_temporary_manifests"
    work_dir.mkdir(parents=True, exist_ok=True)
    tmca_manifest_to_use = args.tmca_manifest
    tmw_manifest_to_use = args.tmw_manifest
    if args.limit_per_protocol is not None:
        tmca_manifest_to_use = work_dir / "tmca_limited_manifest.csv"
        tmw_manifest_to_use = work_dir / "tmw_limited_manifest.csv"
        tmca_manifest.to_csv(tmca_manifest_to_use, index=False)
        tmw_manifest.to_csv(tmw_manifest_to_use, index=False)

    if args.convert == "needed":
        print("\n[1/7] Convert TMCA raw XML files listed in the manifest")
        converted, skipped = _convert_rows(tmca_manifest, repo_root=ROOT, skip_existing=True)
        print(f"TMCA conversion complete. converted={converted}, skipped_existing={skipped}")

        print("\n[2/7] Convert TMW raw XML files listed in the manifest")
        converted, skipped = _convert_rows(tmw_manifest, repo_root=ROOT, skip_existing=True)
        print(f"TMW conversion complete. converted={converted}, skipped_existing={skipped}")
    else:
        print("\n[1-2/7] Conversion skipped by user request.")

    base_out = ROOT / "outputs" / "benny_raw_data"

    print("\n[3/7] Analyze individual TMCA runs")
    tmca_metrics = analyze_tmca_screening(
        ROOT,
        tmca_manifest_to_use,
        base_out / "01_tmca_run_analysis",
        config_path=args.config,
    )
    print(f"TMCA run metrics written for {len(tmca_metrics)} runs.")

    print("\n[4/7] Summarize TMCA screening")
    tmca_summary = summarize_tmca_screening(
        base_out / "01_tmca_run_analysis" / "tmca_run_metrics.csv",
        base_out / "02_tmca_screening_summary",
        config_path=args.config,
    )
    print(f"TMCA summary written for {len(tmca_summary)} condition groups.")

    print("\n[5/7] Make initial TMW V_step plan from TMCA")
    plan = plan_tmw_from_tmca(
        base_out / "02_tmca_screening_summary" / "tmca_screening_summary.csv",
        base_out / "03_tmw_plan_from_tmca" / "recommended_tmw_vstep_plan.csv",
    )
    print(f"TMW planning table written for {len(plan)} condition groups.")

    print("\n[6/7] Analyze individual TMW runs")
    tmw_metrics = analyze_tmw_bracketing(
        ROOT,
        tmw_manifest_to_use,
        base_out / "04_tmw_run_analysis",
        config_path=args.config,
    )
    print(f"TMW run metrics written for {len(tmw_metrics)} runs.")

    print("\n[7/7] Fit and compare TMW conditions")
    try:
        transition_summary = fit_tmw_conditions(
            base_out / "04_tmw_run_analysis" / "tmw_run_metrics.csv",
            base_out / "05_tmw_condition_fits",
            config_path=args.config,
        )
        compare_tmw_conditions(
            base_out / "05_tmw_condition_fits" / "tmw_condition_transition_summary.csv",
            base_out / "06_tmw_condition_comparison",
            config_path=args.config,
        )
        print(f"TMW transition summary written for {len(transition_summary)} condition groups.")
    except Exception as exc:
        # This usually happens only with --limit-per-protocol, because two quick-test
        # TMW rows are not enough to bracket V_C--V_F.  For the full manuscript
        # manifest, this stage should complete normally.
        print("TMW transition fitting/comparison was not completed.")
        print(f"Reason: {exc}")
        if args.limit_per_protocol is not None:
            print("This is expected for a quick limited test. Run again without --limit-per-protocol for final reproduction.")
        else:
            raise

    print("\nDONE.")
    print("Check these folders:")
    print(f"  {base_out / '01_tmca_run_analysis' / 'run_plots'}")
    print(f"  {base_out / '02_tmca_screening_summary'}")
    print(f"  {base_out / '04_tmw_run_analysis' / 'run_plots'}")
    print(f"  {base_out / '05_tmw_condition_fits'}")
    print(f"  {base_out / '06_tmw_condition_comparison'}")


if __name__ == "__main__":
    main()
