"""Weld-start detection and manual selection utilities.

The weld-start coordinate is critical because the weld-length axis is computed
from it.  The workflow supports the same practical options used during the
project:

1. Use an explicit ``weld_start_time_s`` written in the manifest.
2. Manually click the load-rise position and add a user-defined delay.
3. Detect the load-rise position automatically and add the same delay.
4. Use a fixed start time.
"""
from __future__ import annotations

from pathlib import Path
import json
import numpy as np
import pandas as pd

from .config import AnalysisConfig
from .data_io import to_float, text


def detect_load_rise_time(control: pd.DataFrame, *, baseline_s: float = 2.0, delta_n: float = 2.0) -> float:
    """Return the first time where force rises above baseline + delta.

    Parameters
    ----------
    control:
        Standardized control trace with ``time_s`` and ``reaction_force_n``.
    baseline_s:
        Duration at the beginning of the record used to estimate baseline load.
    delta_n:
        Load increase above the baseline required to define the load-rise point.
    """
    if control.empty:
        return np.nan
    t = control["time_s"].to_numpy(float)
    f = control["reaction_force_n"].to_numpy(float)
    t0 = float(np.nanmin(t))
    base_mask = t <= t0 + float(baseline_s)
    if not np.any(base_mask):
        base_mask = np.arange(len(t)) < min(10, len(t))
    baseline = float(np.nanmean(f[base_mask]))
    candidates = np.where(f > baseline + float(delta_n))[0]
    if candidates.size == 0:
        return np.nan
    return float(t[candidates[0]])


def resolve_weld_start_time(row: pd.Series, control: pd.DataFrame, config: AnalysisConfig) -> tuple[float, str, float, float]:
    """Resolve weld-start time and return ``(start, source, load_rise, delay)``.

    The source string is written to the run metrics table for traceability.
    """
    explicit_start = to_float(row.get("weld_start_time_s"))
    manual_load_rise = to_float(row.get("manual_load_rise_time_s"))
    row_delay = to_float(row.get("load_rise_to_weld_start_delay_s"))
    delay = row_delay if np.isfinite(row_delay) else float(config.load_rise_to_weld_start_delay_s)

    if np.isfinite(explicit_start):
        return explicit_start, "manifest_weld_start_time_s", manual_load_rise, delay

    if np.isfinite(manual_load_rise):
        return manual_load_rise + delay, "manual_load_rise_time_s_plus_delay", manual_load_rise, delay

    mode = text(row.get("weld_start_mode")) or config.weld_start_mode
    mode = mode.lower()
    if "fixed" in mode:
        fixed = to_float(row.get("fixed_weld_start_time_s"))
        if not np.isfinite(fixed):
            fixed = float(config.fixed_weld_start_time_s)
        return fixed, "fixed_time", np.nan, delay

    load_rise = detect_load_rise_time(
        control,
        baseline_s=float(row.get("load_rise_baseline_s", config.load_rise_baseline_s)) if str(row.get("load_rise_baseline_s", "")).strip() else config.load_rise_baseline_s,
        delta_n=float(row.get("load_rise_delta_n", config.load_rise_delta_n)) if str(row.get("load_rise_delta_n", "")).strip() else config.load_rise_delta_n,
    )
    if np.isfinite(load_rise):
        return load_rise + delay, "auto_load_rise_plus_delay", load_rise, delay

    return float(config.fixed_weld_start_time_s), "fallback_fixed_time", np.nan, delay


def pick_load_rise_interactive(control: pd.DataFrame, *, title: str = "Select load-rise point") -> float:
    """Open an interactive plot and return the clicked load-rise time.

    This function is intentionally small and easy to edit.  It requires a local
    Python session with an interactive Matplotlib backend.  In the plot, click
    the load-rise point; the script will then add the selected delay and write
    the resulting weld-start time to a new manifest file.
    """
    import matplotlib.pyplot as plt

    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.plot(control["time_s"], control["reaction_force_n"], color="red", lw=1.2, label="reaction force")
    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Reaction force (N)", color="red")
    ax1.tick_params(axis="y", labelcolor="red")
    ax1.grid(True, alpha=0.25)
    ax2 = ax1.twinx()
    ax2.plot(control["time_s"], np.abs(control["actuator_velocity_mm_s"]), color="green", lw=0.9, alpha=0.6, label="velocity")
    ax2.set_ylabel("Transverse velocity (mm/s)", color="green")
    ax2.tick_params(axis="y", labelcolor="green")
    fig.suptitle(title + "\nClick load-rise point; close window or press Enter after click")
    pts = plt.ginput(1, timeout=0)
    plt.close(fig)
    if not pts:
        return np.nan
    return float(pts[0][0])


def load_overrides(path: str | Path) -> dict[str, dict[str, float | str]]:
    """Load saved manual start overrides from JSON."""
    path = Path(path)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_overrides(path: str | Path, overrides: dict[str, dict[str, float | str]]) -> None:
    """Save manual start overrides to JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(overrides, indent=2), encoding="utf-8")
