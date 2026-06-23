"""High-level TMCA -> TMW campaign workflow.

This module connects the reusable analysis functions into the numbered workflow
used by the scripts.  First-time users usually do not need to edit this file.

The important sequence is:

1. analyze individual TMCA runs;
2. summarize TMCA V_NC values;
3. plan first TMW V_step levels;
4. analyze individual TMW runs;
5. fit V_C--V_F for each condition;
6. compare all fitted conditions.

If you want to change the details of a calculation, edit the lower-level files:

- ``run_analysis.py`` for single-run metric extraction;
- ``metrics.py`` for V_NC summaries and V_C--V_F fitting;
- ``plots.py`` for figure appearance.
"""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

from .data_io import load_processed_tmw, load_processed_tmca, write_csv
from .metrics import summarize_tmw_transitions, summarize_tmca_vnc, recommend_tmw_steps_from_tmca, fit_tmw_transition
from .plots import plot_tmw_transition_summary, plot_tmca_vnc_summary, plot_tmw_condition_fit, condition_plot_filename
from .run_analysis import analyze_manifest
from .config import load_config


def _included(df: pd.DataFrame) -> pd.Series:
    """Return True for rows that should be included in campaign summaries.

    The code still analyzes excluded rows at the single-run level.  Exclusion
    only controls whether the row contributes to TMCA/TMW summary values.
    """
    if "include_in_summary" not in df.columns:
        return pd.Series(True, index=df.index)
    return ~df["include_in_summary"].fillna("yes").astype(str).str.lower().isin(["no", "false", "0", "exclude"])


def reproduce_manuscript(repo_root: str | Path, output_dir: str | Path | None = None, config_path: str | Path | None = None) -> None:
    """Reproduce manuscript-level summary figures from processed data.

    Use this function when you want to regenerate the paper figures from the
    already processed CSV files.  It does not reanalyze raw controller logs and
    it does not perform manual weld-start selection.
    """
    repo_root = Path(repo_root)
    config = load_config(config_path)
    output_dir = Path(output_dir) if output_dir is not None else repo_root / "outputs" / "manuscript_reproduction"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load the processed tables that correspond to the submitted manuscript.
    tmw = load_processed_tmw(repo_root / "data" / "processed" / "tmw_oct2025_summary_standardized.csv")
    tmca = load_processed_tmca(repo_root / "data" / "processed" / "tmca_dec2025_summary_standardized.csv")

    # Calculate condition-level summaries and make the two manuscript-style plots.
    tmw_summary = summarize_tmw_transitions(tmw)
    tmca_summary = summarize_tmca_vnc(tmca)
    write_csv(tmw_summary, output_dir / "tmw_transition_summary.csv")
    write_csv(tmca_summary, output_dir / "tmca_vnc_summary.csv")
    plot_tmw_transition_summary(tmw_summary, output_dir / "Transition_ranges_summary.png", config=config)
    plot_tmca_vnc_summary(tmca, output_dir / "TMCA_transition_range_TMWstyle_box.png", config=config)


def analyze_tmca_screening(repo_root: str | Path, manifest_path: str | Path, output_dir: str | Path, config_path: str | Path | None = None) -> pd.DataFrame:
    """Stage 1: analyze individual TMCA screening tests.

    Input: one manifest row per TMCA weld.
    Output: one single-run plot per weld and a ``tmca_run_metrics.csv`` table.
    """
    out = analyze_manifest(manifest_path, output_dir=output_dir, repo_root=repo_root, protocol="TMCA", config_path=config_path)
    write_csv(out, Path(output_dir) / "tmca_run_metrics.csv")
    return out


def summarize_tmca_screening(metrics_path: str | Path, output_dir: str | Path, config_path: str | Path | None = None) -> pd.DataFrame:
    """Stage 2: summarize accepted TMCA V_NC values.

    Run this only after checking the single-run plots from Stage 1.
    The output also includes an initial TMW V_step plan based on the V_NC range.
    """
    output_dir = Path(output_dir)
    config = load_config(config_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics = pd.read_csv(metrics_path)
    tmca = metrics[metrics["protocol"].astype(str).str.upper().eq("TMCA") & _included(metrics)].copy()
    if tmca.empty:
        raise ValueError("No included TMCA rows are available for screening summary.")
    summary = summarize_tmca_vnc(tmca)
    plan = recommend_tmw_steps_from_tmca(summary)
    write_csv(summary, output_dir / "tmca_screening_summary.csv")
    write_csv(plan, output_dir / "recommended_tmw_vstep_plan.csv")
    plot_tmca_vnc_summary(tmca, output_dir / "TMCA_transition_range_TMWstyle_box.png", config=config)
    return summary


def plan_tmw_from_tmca(tmca_summary_path: str | Path, output_csv: str | Path) -> pd.DataFrame:
    """Stage 3: create/recreate an initial TMW V_step plan from TMCA results.

    The resulting V_step values are starting points only.  The TMW campaign must
    still be expanded until no-crack and full-crack endpoints are bracketed.
    """
    summary = pd.read_csv(tmca_summary_path)
    plan = recommend_tmw_steps_from_tmca(summary)
    write_csv(plan, output_csv)
    return plan


def analyze_tmw_bracketing(repo_root: str | Path, manifest_path: str | Path, output_dir: str | Path, config_path: str | Path | None = None) -> pd.DataFrame:
    """Stage 4: analyze individual constant-velocity TMW bracketing tests.

    Input: one manifest row per TMW weld.
    Output: one single-run plot per weld and a ``tmw_run_metrics.csv`` table.
    """
    out = analyze_manifest(manifest_path, output_dir=output_dir, repo_root=repo_root, protocol="TMW", config_path=config_path)
    write_csv(out, Path(output_dir) / "tmw_run_metrics.csv")
    return out


def fit_tmw_conditions(metrics_path: str | Path, output_dir: str | Path, condition_id: str | None = None, config_path: str | Path | None = None) -> pd.DataFrame:
    """Stage 5: fit V_C--V_F for each included TMW condition.

    A condition is defined by ``condition_id``.  All included rows with the same
    ``condition_id`` are fitted together.  If a condition does not contain enough
    V_step values or is not bracketed, the error is written to a warning file so
    the user can perform additional TMW tests.
    """
    output_dir = Path(output_dir)
    config = load_config(config_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    plot_dir = output_dir / "condition_transition_plots"
    plot_dir.mkdir(parents=True, exist_ok=True)
    metrics = pd.read_csv(metrics_path)
    tmw = metrics[metrics["protocol"].astype(str).str.upper().eq("TMW") & _included(metrics)].copy()
    if condition_id:
        tmw = tmw[tmw["condition_id"].astype(str).eq(condition_id)].copy()
    if tmw.empty:
        raise ValueError("No included TMW rows are available for transition fitting.")

    records = []
    warnings = []
    for cid, group in tmw.groupby("condition_id", dropna=False, sort=True):
        try:
            fit = fit_tmw_transition(group["v_step_mm_s"], group["l_star"])
            row0 = group.iloc[0]
            rec = {
                "condition_id": cid,
                "base_material": row0.get("base_material"),
                "filler_material": row0.get("filler_material"),
                "preheat_c": row0.get("preheat_c", np.nan),
                "current_a": float(row0.get("current_a")) if np.isfinite(pd.to_numeric(pd.Series([row0.get("current_a")]), errors="coerce").iloc[0]) else np.nan,
                "n_runs": int(len(group)),
                "n_v_steps": int(pd.Series(group["v_step_mm_s"]).dropna().nunique()),
                "v_c_mm_s": fit.v_c_mm_s,
                "v_f_mm_s": fit.v_f_mm_s,
                "transition_width_mm_s": fit.transition_width_mm_s,
                "fit_mode": fit.fit_mode,
            }
            records.append(rec)
            plot_tmw_condition_fit(group, rec, plot_dir / condition_plot_filename(cid), config=config)
        except Exception as exc:
            warnings.append(f"{cid}: {exc}")

    out = pd.DataFrame.from_records(records)
    if not out.empty:
        out = out.sort_values(["base_material", "current_a", "v_c_mm_s"], na_position="last").reset_index(drop=True)
    write_csv(out, output_dir / "tmw_condition_transition_summary.csv")
    if warnings:
        (output_dir / "tmw_condition_fit_warnings.txt").write_text("\n".join(warnings) + "\n", encoding="utf-8")
    return out


def compare_tmw_conditions(transition_summary_path: str | Path, output_dir: str | Path, config_path: str | Path | None = None) -> pd.DataFrame:
    """Stage 6: compare fitted V_C--V_F intervals across several conditions."""
    output_dir = Path(output_dir)
    config = load_config(config_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = pd.read_csv(transition_summary_path)
    if summary.empty:
        raise ValueError("The transition summary table is empty.")
    plot_tmw_transition_summary(summary, output_dir / "Transition_ranges_summary.png", config=config)
    write_csv(summary, output_dir / "tmw_condition_comparison_summary.csv")
    return summary
