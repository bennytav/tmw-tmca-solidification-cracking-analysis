"""Campaign-level metric extraction for TMW/TMCA weldability analysis.

This module contains the mathematical definitions used after the run-level
analysis is complete.  It does not read raw controller files and it does not
measure cracks from images.  It works on run-level tables that already contain:

- TMW: ``v_step_mm_s`` and ``l_star`` for each weld.
- TMCA: ``v_nc_mm_s`` for each weld.

Change this module only when you want to change how the campaign-level metrics
are defined, for example the TMW transition fitting method or the way TMW step
levels are recommended from TMCA screening data.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
import numpy as np
import pandas as pd

from .data_io import condition_id_from_values


@dataclass(frozen=True)
class TransitionFit:
    """Constant-velocity TMW transition fit."""
    v_c_mm_s: float
    v_f_mm_s: float
    transition_width_mm_s: float
    fit_mode: str


def piecewise_transition(v: Iterable[float], v_c: float, v_f: float) -> np.ndarray:
    """Piecewise linear TMW transition model for normalized crack length L*."""
    v = np.asarray(v, dtype=float)
    if v_f <= v_c:
        return (v >= v_c).astype(float)
    return np.clip((v - v_c) / (v_f - v_c), 0.0, 1.0)


def _huber_loss(residual: np.ndarray, k: float = 0.15) -> np.ndarray:
    a = np.abs(residual)
    return np.where(a <= k, 0.5 * residual**2, k * (a - 0.5 * k))


def _measured_bracket(v: np.ndarray, l_star: np.ndarray) -> tuple[float, float]:
    """Estimate measured no-crack/full-crack bracket before model fitting."""
    no_crack = l_star <= 0.02
    full_crack = l_star >= 0.98
    if np.any(no_crack) and np.any(full_crack):
        vc = float(np.max(v[no_crack]))
        vf = float(np.min(v[full_crack]))
        if vf >= vc:
            return vc, vf
    low = v[l_star <= 0.20]
    high = v[l_star >= 0.80]
    if low.size and high.size:
        vc = float(np.median(low))
        vf = float(np.median(high))
        return min(vc, vf), max(vc, vf)
    raise ValueError("TMW transition is not bracketed. Add lower/higher V_step tests.")


def fit_tmw_transition(v_step_mm_s: Iterable[float], l_star: Iterable[float], *, grid_points: int = 100) -> TransitionFit:
    """Fit ``V_C`` and ``V_F`` from TMW runs at several ``V_step`` levels.

    Required input for one condition:

    - several constant-velocity TMW runs;
    - one ``V_step`` value per run;
    - one normalized crack length ``L*`` per run.

    The function first checks that the measured data bracket the transition.
    If the condition does not include both low-crack and high-crack responses,
    the function raises an error and the user should perform more TMW tests.
    """
    v = np.asarray(list(v_step_mm_s), dtype=float)
    y = np.clip(np.asarray(list(l_star), dtype=float), 0.0, 1.0)
    mask = np.isfinite(v) & np.isfinite(y)
    v = v[mask]
    y = y[mask]
    if v.size < 3:
        raise ValueError("At least three TMW runs are needed for a transition fit.")
    order = np.argsort(v)
    v = v[order]
    y = y[order]
    vc0, vf0 = _measured_bracket(v, y)
    if vf0 <= vc0:
        return TransitionFit(vc0, vf0, max(0.0, vf0 - vc0), "measured")

    # Search close to the measured bracket to keep the fit descriptive rather than extrapolative.
    width = max(1e-6, vf0 - vc0)
    vc_grid = np.linspace(max(float(v.min()), vc0 - 0.10 * width), min(float(v.max()), vc0 + 0.10 * width), grid_points)
    vf_grid = np.linspace(max(float(v.min()), vf0 - 0.10 * width), min(float(v.max()), vf0 + 0.10 * width), grid_points)
    best = (np.inf, vc0, vf0)
    for vc in vc_grid:
        for vf in vf_grid:
            if vf <= vc:
                continue
            loss = float(np.sum(_huber_loss(y - piecewise_transition(v, vc, vf))))
            if loss < best[0]:
                best = (loss, float(vc), float(vf))
    vc = max(best[1], vc0)
    vf = min(best[2], vf0)
    if vf < vc:
        vc, vf = vc0, vf0
        mode = "measured"
    else:
        mode = "piecewise_huber_fit"
    return TransitionFit(vc, vf, vf - vc, mode)


def classify_lstar(l_star: float) -> str:
    """Classify a TMW run from L*."""
    if not np.isfinite(l_star):
        return ""
    if l_star <= 0.02:
        return "no crack"
    if l_star >= 0.98:
        return "full crack"
    return "partial"


def summarize_tmw_transitions(df: pd.DataFrame) -> pd.DataFrame:
    """Fit and summarize ``V_C``/``V_F`` for every TMW condition.

    Rows are grouped by ``condition_id``.  Therefore, a new material or filler
    does not require code changes; only the manifest ``condition_id`` must be
    filled consistently.
    """
    work = df.copy()
    if "condition_id" not in work.columns or work["condition_id"].fillna("").eq("").any():
        work["condition_id"] = work.apply(lambda r: condition_id_from_values(r["base_material"], r["filler_material"], r["current_a"], r.get("preheat_c")), axis=1)
    records: list[dict] = []
    for cid, group in work.groupby("condition_id", dropna=False, sort=True):
        fit = fit_tmw_transition(group["v_step_mm_s"], group["l_star"])
        row = group.iloc[0]
        records.append({
            "condition_id": cid,
            "base_material": row.get("base_material"),
            "filler_material": row.get("filler_material"),
            "preheat_c": row.get("preheat_c", np.nan),
            "current_a": float(row.get("current_a")) if np.isfinite(pd.to_numeric(pd.Series([row.get("current_a")]), errors="coerce").iloc[0]) else np.nan,
            "n_runs": int(len(group)),
            "n_v_steps": int(pd.Series(group["v_step_mm_s"]).dropna().nunique()),
            "v_c_mm_s": fit.v_c_mm_s,
            "v_f_mm_s": fit.v_f_mm_s,
            "transition_width_mm_s": fit.transition_width_mm_s,
            "fit_mode": fit.fit_mode,
        })
    out = pd.DataFrame.from_records(records)
    if out.empty:
        return out
    return out.sort_values(["base_material", "current_a", "v_c_mm_s"], na_position="last").reset_index(drop=True)


def summarize_tmca_vnc(df: pd.DataFrame, *, exclude_load_increase_no: bool = False) -> pd.DataFrame:
    """Summarize TMCA ``V_NC`` values by condition.

    This is a screening summary.  ``V_NC`` should be used to plan useful TMW
    ``V_step`` levels; it is not treated as the same metric as ``V_C``.
    """
    work = df.copy()
    if exclude_load_increase_no and "load_increase_acceptance" in work.columns:
        work = work[work["load_increase_acceptance"].astype(str).str.lower() != "no"].copy()
    if "condition_id" not in work.columns or work["condition_id"].fillna("").eq("").any():
        work["condition_id"] = work.apply(lambda r: condition_id_from_values(r["base_material"], r["filler_material"], r["current_a"], r.get("preheat_c")), axis=1)
    records: list[dict] = []
    for cid, group in work.groupby("condition_id", dropna=False, sort=True):
        vals = pd.to_numeric(group["v_nc_mm_s"], errors="coerce").dropna()
        if vals.empty:
            continue
        row = group.iloc[0]
        records.append({
            "condition_id": cid,
            "base_material": row.get("base_material"),
            "filler_material": row.get("filler_material"),
            "current_a": float(row.get("current_a")) if np.isfinite(pd.to_numeric(pd.Series([row.get("current_a")]), errors="coerce").iloc[0]) else np.nan,
            "preheat_c": row.get("preheat_c", np.nan),
            "spacer_mm": row.get("spacer_mm", np.nan),
            "n_runs": int(vals.size),
            "v_nc_mean_mm_s": float(vals.mean()),
            "v_nc_sd_mm_s": float(vals.std(ddof=1)) if vals.size > 1 else np.nan,
            "v_nc_min_mm_s": float(vals.min()),
            "v_nc_max_mm_s": float(vals.max()),
        })
    out = pd.DataFrame.from_records(records)
    if out.empty:
        return out
    return out.sort_values(["base_material", "current_a", "v_nc_mean_mm_s"], na_position="last").reset_index(drop=True)


def recommend_tmw_steps_from_tmca(tmca_summary: pd.DataFrame, *, padding_mm_s: float = 0.015, round_to: float = 0.005) -> pd.DataFrame:
    """Recommend initial constant-Vstep TMW levels from TMCA V_NC results.

    The output is a starting plan only. V_NC is not identical to V_C, so the TMW
    series must still be expanded until no-crack and full-crack endpoints are
    bracketed.
    """
    records: list[dict] = []
    for _, row in tmca_summary.iterrows():
        low = float(row["v_nc_min_mm_s"])
        mean = float(row["v_nc_mean_mm_s"])
        high = float(row["v_nc_max_mm_s"])
        raw = [max(0.001, low - padding_mm_s), low, mean, high, high + padding_mm_s]
        steps = sorted({round(x / round_to) * round_to for x in raw if np.isfinite(x)})
        while len(steps) < 5:
            steps.append(round((steps[-1] + padding_mm_s) / round_to) * round_to)
        for i, step in enumerate(steps[:5], start=1):
            records.append({
                "condition_id": row["condition_id"],
                "base_material": row.get("base_material"),
                "filler_material": row.get("filler_material"),
                "current_a": row.get("current_a"),
                "tmca_v_nc_mean_mm_s": mean,
                "suggested_order": i,
                "suggested_v_step_mm_s": float(step),
                "reason": "initial TMW bracketing around TMCA V_NC range",
            })
    return pd.DataFrame.from_records(records)

# Compatibility helper used for run-level TMW classification.
def classify_tmw_crack_state(l_star: float) -> str:
    try:
        val = float(l_star)
    except Exception:
        return "unknown"
    if not np.isfinite(val):
        return "unknown"
    if val <= 0.02:
        return "no crack"
    if val >= 0.98:
        return "full crack"
    return "partial crack"
