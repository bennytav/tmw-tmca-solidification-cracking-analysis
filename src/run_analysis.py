"""Run-level analysis for individual TMW and TMCA welds.

This module is the best place to start when you want to understand how one
single weld is converted into numerical metrics.  The analysis intentionally
uses two inputs:

1. one controller CSV file containing time-series signals; and
2. one manifest row containing experimental metadata and crack measurements.

The controller CSV alone cannot give the final crack length, because the crack
end is measured from images/CT after welding.  The manifest therefore remains
the traceability file that connects the control record to the measured crack
geometry.
"""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

from .config import load_config, row_value
from .data_io import load_control_csv, load_run_manifest, to_float, text, write_csv
from .metrics import classify_lstar
from .plots import plot_single_run_control
from .schema import RUN_METRIC_COLUMNS


def resolve_control_path(control_csv: object, *, manifest_path: str | Path, repo_root: str | Path | None = None) -> Path:
    """Resolve the control CSV path stored in the manifest.

    The path may be absolute, relative to the manifest folder, or relative to
    the repository root.  This makes the project portable between computers.
    """
    p = Path(text(control_csv))
    if p.is_absolute():
        return p
    manifest_dir = Path(manifest_path).resolve().parent
    by_manifest = manifest_dir / p
    if by_manifest.exists():
        return by_manifest
    if repo_root is not None:
        by_repo = Path(repo_root).resolve() / p
        if by_repo.exists():
            return by_repo
    return by_manifest


def _first_finite(*values: object) -> float:
    for value in values:
        f = to_float(value)
        if np.isfinite(f):
            return f
    return np.nan


def detect_load_rise_time(control: pd.DataFrame, *, baseline_window_s: float = 2.0, load_rise_delta_n: float = 2.0) -> float:
    """Detect the first time at which the load rises above the early baseline.

    This is intentionally simple and transparent.  If the automatic result is
    not correct, set ``weld_start_method=manual_load_rise`` and provide
    ``manual_load_rise_time_s`` in the manifest, or use ``scripts/09_pick_weld_start.py``.
    """
    if control.empty:
        return np.nan
    t = pd.to_numeric(control["time_s"], errors="coerce")
    f = pd.to_numeric(control["reaction_force_n"], errors="coerce")
    t0 = float(np.nanmin(t))
    baseline_mask = t <= t0 + float(baseline_window_s)
    baseline = float(np.nanmean(f[baseline_mask])) if baseline_mask.any() else float(np.nanmean(f.iloc[:10]))
    threshold = baseline + float(load_rise_delta_n)
    candidates = control.loc[f > threshold]
    if candidates.empty:
        return np.nan
    return float(candidates.iloc[0]["time_s"])


def determine_weld_start_time(control: pd.DataFrame, row: pd.Series, config: dict) -> tuple[float, str, str, float, float]:
    """Determine weld-start time using manifest, manual load-rise, auto load-rise, or fixed time.

    Returns
    -------
    weld_start_time_s, source_label, method, manual_load_rise_time_s, delay_s
    """
    start_cfg = config.get("start_detection", {})
    method = text(row_value(row, "weld_start_method", start_cfg.get("default_method", "manifest_or_load_rise"))).lower()
    if not method:
        method = "manifest_or_load_rise"

    manifest_start = to_float(row.get("weld_start_time_s"))
    manual_rise = to_float(row.get("manual_load_rise_time_s"))
    fixed_start = _first_finite(row.get("fixed_start_time_s"), start_cfg.get("fixed_start_time_s"))
    manual_delay = _first_finite(row.get("manual_load_to_start_delay_s"), start_cfg.get("manual_load_to_start_delay_s", 3.0))
    auto_delay = _first_finite(row.get("auto_load_to_start_delay_s"), start_cfg.get("auto_load_to_start_delay_s", 0.0))
    baseline_s = _first_finite(row.get("load_baseline_window_s"), start_cfg.get("baseline_window_s", 2.0))
    delta_n = _first_finite(row.get("load_rise_delta_n"), start_cfg.get("load_rise_delta_n", 2.0))

    if method in {"manifest", "given", "weld_start_time"}:
        if not np.isfinite(manifest_start):
            raise ValueError("weld_start_method=manifest requires weld_start_time_s.")
        return manifest_start, "manifest weld_start_time_s", method, manual_rise, manual_delay

    if method in {"manual", "manual_load", "manual_load_rise"}:
        if not np.isfinite(manual_rise):
            raise ValueError("weld_start_method=manual_load_rise requires manual_load_rise_time_s.")
        return manual_rise + manual_delay, f"manual load rise + {manual_delay:g} s", "manual_load_rise", manual_rise, manual_delay

    if method in {"fixed", "fixed_time"}:
        if not np.isfinite(fixed_start):
            raise ValueError("weld_start_method=fixed_time requires fixed_start_time_s.")
        return fixed_start, "fixed_start_time_s", "fixed_time", manual_rise, manual_delay

    if method in {"load", "load_rise", "auto_load_rise"}:
        rise = detect_load_rise_time(control, baseline_window_s=baseline_s, load_rise_delta_n=delta_n)
        if not np.isfinite(rise):
            raise ValueError("Automatic load-rise detection failed; use manual_load_rise_time_s or weld_start_time_s.")
        return rise + auto_delay, f"auto load rise + {auto_delay:g} s", "auto_load_rise", rise, auto_delay

    # Default: use manifest if available; otherwise use automatic load-rise.
    if np.isfinite(manifest_start):
        return manifest_start, "manifest weld_start_time_s", "manifest_or_load_rise", manual_rise, manual_delay
    if np.isfinite(manual_rise):
        return manual_rise + manual_delay, f"manual load rise + {manual_delay:g} s", "manual_load_rise", manual_rise, manual_delay
    rise = detect_load_rise_time(control, baseline_window_s=baseline_s, load_rise_delta_n=delta_n)
    if np.isfinite(rise):
        return rise + auto_delay, f"auto load rise + {auto_delay:g} s", "auto_load_rise", rise, auto_delay
    if np.isfinite(fixed_start):
        return fixed_start, "fixed_start_time_s", "fixed_time", manual_rise, manual_delay
    raise ValueError("Could not determine weld start. Supply weld_start_time_s or manual_load_rise_time_s.")


def _trim_to_force(control: pd.DataFrame, trim_force_n: float) -> pd.DataFrame:
    """Keep rows up to the first target force, if requested."""
    if not np.isfinite(trim_force_n) or "reaction_force_n" not in control.columns:
        return control
    idx = control.index[control["reaction_force_n"] >= trim_force_n]
    if len(idx) == 0:
        return control
    return control.loc[:idx[0]].copy()


def ensure_weld_length(control: pd.DataFrame, row: pd.Series, config: dict) -> tuple[pd.DataFrame, dict]:
    """Return control data with a valid ``weld_length_mm`` axis.

    If the controller CSV already contains ``weld_length_mm``, that coordinate
    is used.  Otherwise the coordinate is calculated from time, weld-start time,
    and welding travel speed:

        weld_length_mm = (time_s - weld_start_time_s) * weld_travel_speed_mm_s

    Because this equation depends directly on ``weld_start_time_s``, the weld
    start should be checked carefully for each new run.
    """
    out = control.copy()
    trim_force_n = _first_finite(row.get("trim_force_n"), config.get("analysis", {}).get("trim_force_n"))
    out = _trim_to_force(out, trim_force_n)

    start_time, source, method, manual_rise, delay = determine_weld_start_time(out, row, config)
    if "weld_length_mm" in out.columns and out["weld_length_mm"].notna().any():
        out["weld_length_mm"] = pd.to_numeric(out["weld_length_mm"], errors="coerce")
        out = out.dropna(subset=["weld_length_mm"]).sort_values("weld_length_mm").reset_index(drop=True)
    else:
        travel = _first_finite(row.get("weld_travel_speed_mm_s"), config.get("analysis", {}).get("default_weld_travel_speed_mm_s"))
        if not np.isfinite(travel):
            raise ValueError("weld_length_mm is missing and weld_travel_speed_mm_s/default_weld_travel_speed_mm_s is not defined.")
        out["weld_length_mm"] = (out["time_s"] - start_time) * travel
        out = out.sort_values("weld_length_mm").reset_index(drop=True)
    start_info = {
        "weld_start_time_s": float(start_time),
        "weld_start_source": source,
        "weld_start_method": method,
        "manual_load_rise_time_s": manual_rise,
        "manual_load_to_start_delay_s": delay,
    }
    return out, start_info


def interpolate_trace_value(control: pd.DataFrame, x_mm: float, column: str) -> float:
    """Interpolate a signal at a specified weld-length coordinate."""
    if not np.isfinite(x_mm) or column not in control.columns:
        return np.nan
    work = control[["weld_length_mm", column]].dropna().sort_values("weld_length_mm")
    if work.empty:
        return np.nan
    x = work["weld_length_mm"].to_numpy(float)
    y = work[column].to_numpy(float)
    if x_mm < np.nanmin(x) or x_mm > np.nanmax(x):
        return np.nan
    return float(np.interp(x_mm, x, y))


def choose_crack_end(row: pd.Series, config: dict) -> tuple[float, str]:
    """Select the crack-end coordinate used for TMCA velocity mapping.

    The default preference is configured in ``config/default_analysis_config.json``.
    The usual choice is ``l_surf_mm`` because the method is designed for surface
    crack-end screening.  If CT validation is used, the user may change the
    preference to use ``l_ct_mm`` first.
    """
    preference = config.get("analysis", {}).get("crack_end_preference", ["l_surf_mm", "l_crack_mm", "l_ct_mm"])
    if isinstance(preference, str):
        preference = [s.strip() for s in preference.split(",") if s.strip()]
    for col in preference:
        value = to_float(row.get(col))
        if np.isfinite(value):
            return value, col
    return np.nan, ""


def _temperature_columns(control: pd.DataFrame) -> list[str]:
    return [c for c in control.columns if c.lower().startswith("temperature_") and c.lower().endswith("_c")]


def _temperature_metrics(control: pd.DataFrame, weld_start_time_s: float) -> tuple[float, float]:
    cols = _temperature_columns(control)
    if not cols:
        return np.nan, np.nan
    temp = control[cols].apply(pd.to_numeric, errors="coerce")
    max_temp = float(np.nanmax(temp.to_numpy(float))) if temp.notna().any().any() else np.nan
    pre = control["time_s"] < weld_start_time_s
    mean_pre = float(np.nanmean(temp.loc[pre].to_numpy(float))) if pre.any() and temp.loc[pre].notna().any().any() else np.nan
    return mean_pre, max_temp


def analyze_one_run(row: pd.Series, *, manifest_path: str | Path, repo_root: str | Path | None = None, output_plot_dir: str | Path | None = None, config: dict | None = None) -> dict:
    """Analyze one weld from one manifest row.

    This function performs the run-level workflow:

    1. load the controller CSV;
    2. define the weld-length coordinate;
    3. read crack measurements from the manifest;
    4. calculate ``L*`` for TMW or ``V_NC`` for TMCA;
    5. extract force/temperature diagnostics;
    6. save a single-run control plot for visual checking.

    Edit this function only if you want to change the definition of run-level
    metrics.  Edit ``plots.py`` if you only want to change plot appearance.
    """
    config = load_config(None) if config is None else config
    protocol = text(row.get("protocol")).upper()
    run_id = text(row.get("run_id"))
    control_path = resolve_control_path(row.get("control_csv"), manifest_path=manifest_path, repo_root=repo_root)
    if not control_path.exists():
        raise FileNotFoundError(f"Run {run_id}: control CSV not found: {control_path}")
    # Load the controller time series and convert it to a weld-length axis.
    # ``raw_control`` stays in time coordinates.  ``control`` contains
    # ``weld_length_mm`` and is used for plotting/interpolation.
    raw_control = load_control_csv(control_path)
    control, start_info = ensure_weld_length(raw_control, row, config)

    # Crack-length measurements come from image/CT measurements written in the
    # manifest.  They are not inferred from the controller signals.
    l_weld = to_float(row.get("l_weld_mm"))
    l_crack = to_float(row.get("l_crack_mm"))
    l_surf = to_float(row.get("l_surf_mm"))
    l_ct = to_float(row.get("l_ct_mm"))
    crack_end, crack_end_source = choose_crack_end(row, config)

    l_star = to_float(row.get("l_star"))
    # For TMW, normalized crack length is the main response variable.  If the
    # user did not enter L* directly, calculate it from L_crack/L_weld.
    if not np.isfinite(l_star) and np.isfinite(l_weld) and l_weld > 0:
        length = l_crack if np.isfinite(l_crack) else l_surf
        if np.isfinite(length):
            l_star = float(np.clip(length / l_weld, 0.0, 1.0))

    # For TMCA, V_NC is obtained by mapping the crack-end coordinate onto the
    # recorded velocity history.  A value entered in the manifest is respected;
    # otherwise the code calculates it by interpolation.
    v_nc = to_float(row.get("v_nc_mm_s"))
    if protocol == "TMCA" and not np.isfinite(v_nc):
        v_nc = abs(interpolate_trace_value(control, crack_end, "actuator_velocity_mm_s"))

    max_force = float(np.nanmax(control["reaction_force_n"].to_numpy(float))) if len(control) else np.nan
    force_at_crack_end = interpolate_trace_value(control, crack_end, "reaction_force_n")
    crack_state = text(row.get("crack_state"))
    if protocol == "TMW" and not crack_state:
        crack_state = classify_lstar(l_star)
    mean_pre_temp, max_temp = _temperature_metrics(raw_control, start_info["weld_start_time_s"])

    metrics = {
        "run_id": run_id,
        "protocol": protocol,
        "test_date_iso": text(row.get("test_date_iso")),
        "condition_id": text(row.get("condition_id")),
        "material_category": text(row.get("material_category")),
        "base_material": text(row.get("base_material")) or "Unknown",
        "filler_material": text(row.get("filler_material")) or "Autogenous",
        "weld_process": text(row.get("weld_process")),
        "current_a": to_float(row.get("current_a")),
        "voltage_v": to_float(row.get("voltage_v")),
        "heat_input_kj_mm": to_float(row.get("heat_input_kj_mm")),
        "shielding_gas": text(row.get("shielding_gas")),
        "preheat_c": to_float(row.get("preheat_c")),
        "spacer_mm": to_float(row.get("spacer_mm")),
        "sheet_thickness_mm": _first_finite(row.get("sheet_thickness_mm"), config.get("plotting", {}).get("sheet_thickness_mm")),
        "k_factor": _first_finite(row.get("k_factor"), config.get("plotting", {}).get("k_factor", 0.707)),
        "v_high_mm_s": to_float(row.get("v_high_mm_s")),
        "v_step_mm_s": to_float(row.get("v_step_mm_s")),
        "a_dec_mm_s2": to_float(row.get("a_dec_mm_s2")),
        "weld_start_method": start_info["weld_start_method"],
        "weld_start_source": start_info["weld_start_source"],
        "manual_load_rise_time_s": start_info["manual_load_rise_time_s"],
        "manual_load_to_start_delay_s": start_info["manual_load_to_start_delay_s"],
        "weld_start_time_s": start_info["weld_start_time_s"],
        "weld_end_time_s": to_float(row.get("weld_end_time_s")),
        "weld_travel_speed_mm_s": _first_finite(row.get("weld_travel_speed_mm_s"), config.get("analysis", {}).get("default_weld_travel_speed_mm_s")),
        "speed_transition_weld_length_mm": to_float(row.get("speed_transition_weld_length_mm")),
        "deceleration_start_weld_length_mm": to_float(row.get("deceleration_start_weld_length_mm")),
        "l_weld_mm": l_weld,
        "l_crack_mm": l_crack,
        "l_surf_mm": l_surf,
        "l_ct_mm": l_ct,
        "crack_end_source": crack_end_source,
        "l_star": l_star,
        "v_nc_mm_s": v_nc,
        "crack_state": crack_state,
        "load_increase_acceptance": text(row.get("load_increase_acceptance")),
        "include_in_summary": text(row.get("include_in_summary")) or "yes",
        "max_force_n": max_force,
        "force_at_crack_end_n": force_at_crack_end,
        "mean_preweld_temperature_c": mean_pre_temp,
        "max_temperature_c": max_temp,
        "show_temperature": text(row.get("show_temperature")),
        "temperature_columns": text(row.get("temperature_columns")),
        "control_csv": str(control_path),
        "notes": text(row.get("notes")),
    }
    if output_plot_dir is not None:
        Path(output_plot_dir).mkdir(parents=True, exist_ok=True)
        plot_single_run_control(control, metrics, Path(output_plot_dir) / f"{run_id}_control_trace.png", config=config)
    return metrics


def analyze_manifest(manifest_path: str | Path, *, output_dir: str | Path, repo_root: str | Path | None = None, protocol: str | None = None, config_path: str | Path | None = None) -> pd.DataFrame:
    """Analyze all rows in a manifest, optionally filtering by protocol.

    This is used by the numbered workflow scripts.  It writes both:

    - ``run_metrics.csv``: generic metrics for all selected rows; and
    - protocol-specific files such as ``tmca_run_metrics.csv`` or
      ``tmw_run_metrics.csv`` through the workflow layer.
    """
    config = load_config(config_path)
    manifest_path = Path(manifest_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = load_run_manifest(manifest_path)
    if protocol is not None:
        protocol_u = protocol.upper()
        manifest = manifest[manifest["protocol"].astype(str).str.upper().eq(protocol_u)].copy()
        if manifest.empty:
            raise ValueError(f"No {protocol_u} rows found in {manifest_path}")
    records = []
    plot_dir = output_dir / "run_plots"
    for _, row in manifest.iterrows():
        records.append(analyze_one_run(row, manifest_path=manifest_path, repo_root=repo_root, output_plot_dir=plot_dir, config=config))
    out = pd.DataFrame.from_records(records)
    for col in RUN_METRIC_COLUMNS:
        if col not in out.columns:
            out[col] = np.nan
    out = out[RUN_METRIC_COLUMNS]
    write_csv(out, output_dir / "run_metrics.csv")
    return out
