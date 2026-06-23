"""Input/output helpers for TMW/TMCA datasets."""
from __future__ import annotations

from pathlib import Path
import re
import numpy as np
import pandas as pd

from .schema import CONTROL_REQUIRED, MANIFEST_REQUIRED, MANIFEST_RECOMMENDED


def text(value: object) -> str:
    """Return a clean string, using an empty string for missing values."""
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return str(value).strip()


def to_float(value: object) -> float:
    """Return a finite float or NaN."""
    try:
        out = float(value)
    except Exception:
        return np.nan
    return out if np.isfinite(out) else np.nan


def normalize_material(value: object) -> str:
    """Normalize a material label without restricting it to a known alloy list."""
    raw = text(value)
    if not raw:
        return "Unknown"
    # Keep user-supplied alloy names, but standardize a few common spacings.
    raw = raw.replace("Al ", "AA") if raw.lower().startswith("al ") else raw
    return raw


def normalize_filler(value: object) -> str:
    """Normalize common filler labels while allowing arbitrary filler names."""
    raw = text(value)
    low = raw.lower().replace(" ", "").replace("-", "").replace("_", "")
    if low in {"", "none", "nan", "nowire", "autogenous", "nofiller", "noﬁller"}:
        return "Autogenous"
    if low in {"5356", "er5356"}:
        return "ER5356"
    if low in {"7075tic", "tic", "7075nanotic", "7075ticnanoparticle"}:
        return "7075TiC"
    return raw


def _safe_token(value: object) -> str:
    token = re.sub(r"[^A-Za-z0-9]+", "", text(value))
    return token or "Unknown"


def condition_id_from_values(base_material: object, filler_material: object, current_a: object = None, preheat_c: object = None, extra: object = None) -> str:
    """Create a stable condition identifier from material/process variables.

    The function is generic: ``base_material`` may be AA5083, 304L, Inconel 718,
    or any other user-defined material label.
    """
    base = _safe_token(normalize_material(base_material))
    filler = _safe_token(normalize_filler(filler_material))
    parts = [base, filler]
    current = to_float(current_a)
    if np.isfinite(current):
        parts.append(f"{int(round(current))}A")
    else:
        cur = _safe_token(current_a)
        if cur and cur != "Unknown":
            parts.append(cur)
    preheat = to_float(preheat_c)
    if np.isfinite(preheat):
        parts.append(f"{preheat:g}Cpreheat")
    ext = _safe_token(extra)
    if ext and ext != "Unknown":
        parts.append(ext)
    return "_".join(parts)


_CONTROL_ALIASES = {
    "time_s": ["time_s", "time [s]", "time", "t", "t_s"],
    "actuator_position_mm": ["actuator_position_mm", "motorpos", "motor pos", "motor position", "position_mm", "position [mm]", "pos_mm"],
    "actuator_velocity_mm_s": ["actuator_velocity_mm_s", "velocity [mm/s]", "velocity", "vel", "v_mm_s", "transverse_velocity_mm_s"],
    "reaction_force_n": ["reaction_force_n", "loadcell", "load cell", "load [n]", "load_n", "force", "force_n", "reaction force [n]"],
    "weld_length_mm": ["weld_length_mm", "weldlen [mm]", "weldlen", "weld length [mm]", "weld_length", "x_weld_mm"],
}


def _normalize_column_key(name: object) -> str:
    return str(name).strip().lower().replace("_", " ").replace("-", " ").replace("  ", " ")


def _standardize_control_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename common controller-column variants to the public schema."""
    rename: dict[str, str] = {}
    norm_to_original = {_normalize_column_key(c): c for c in df.columns}
    for target, aliases in _CONTROL_ALIASES.items():
        if target in df.columns:
            continue
        for alias in aliases:
            key = _normalize_column_key(alias)
            if key in norm_to_original:
                rename[norm_to_original[key]] = target
                break
    # Temper_1, Temper_2, etc. are converted to temperature_1_c, ...
    for c in df.columns:
        key = _normalize_column_key(c)
        m = re.match(r"(?:temper|temp|temperature)\s*([0-9]+)", key)
        if m:
            rename.setdefault(c, f"temperature_{m.group(1)}_c")
    if rename:
        df = df.rename(columns=rename)
    return df


def load_control_csv(path: str | Path) -> pd.DataFrame:
    """Load one standardized controller CSV file.

    Required signals are time, actuator position, actuator velocity, and
    reaction force.  Common column names from the original TMW/TMCA scripts are
    accepted and renamed automatically.
    """
    path = Path(path)
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    df = _standardize_control_columns(df)
    missing = CONTROL_REQUIRED.difference(df.columns)
    if missing:
        raise ValueError(f"Control CSV {path} is missing columns: {sorted(missing)}")
    for col in df.columns:
        low = col.lower()
        if low.endswith(("_s", "_mm", "_mm_s", "_mm_s2", "_n", "_c")) or col in CONTROL_REQUIRED:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=["time_s", "actuator_velocity_mm_s", "reaction_force_n"]).reset_index(drop=True)


def load_run_manifest(path: str | Path) -> pd.DataFrame:
    """Load a run manifest and normalize common labels/units.

    Only ``run_id``, ``protocol`` and ``control_csv`` are required.  The other
    columns are recommended and are added as blank columns if missing.  This
    allows the same workflow to be used for any alloy and welding condition.
    """
    path = Path(path)
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    missing = MANIFEST_REQUIRED.difference(df.columns)
    if missing:
        raise ValueError(f"Manifest {path} is missing columns: {sorted(missing)}")
    for col in MANIFEST_RECOMMENDED:
        if col not in df.columns:
            df[col] = ""
    df["protocol"] = df["protocol"].astype(str).str.upper().str.strip()
    df["base_material"] = df["base_material"].map(normalize_material)
    df["filler_material"] = df["filler_material"].map(normalize_filler)
    numeric_cols = [
        "current_a", "voltage_v", "heat_input_kj_mm", "preheat_c", "spacer_mm",
        "sheet_thickness_mm", "k_factor", "v_high_mm_s", "v_step_mm_s",
        "a_dec_mm_s2", "weld_start_time_s", "manual_load_rise_time_s",
        "manual_load_to_start_delay_s", "fixed_start_time_s", "load_rise_delta_n",
        "load_baseline_window_s", "weld_end_time_s", "weld_travel_speed_mm_s",
        "speed_transition_weld_length_mm", "deceleration_start_weld_length_mm",
        "l_weld_mm", "l_crack_mm", "l_surf_mm", "l_ct_mm", "l_star",
        "v_nc_mm_s",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["include_in_summary"] = df["include_in_summary"].fillna("yes").astype(str).str.strip().str.lower()
    blank_condition = df["condition_id"].fillna("").astype(str).str.strip().eq("")
    df.loc[blank_condition, "condition_id"] = df[blank_condition].apply(
        lambda r: condition_id_from_values(r["base_material"], r["filler_material"], r.get("current_a"), r.get("preheat_c")), axis=1
    )
    return df


def load_processed_tmw(path: str | Path) -> pd.DataFrame:
    """Load the processed manuscript TMW table."""
    df = pd.read_csv(path)
    if "base_material" not in df.columns:
        df["base_material"] = "Unknown"
    if "filler_material" not in df.columns:
        df["filler_material"] = "Autogenous"
    df["base_material"] = df["base_material"].map(normalize_material)
    df["filler_material"] = df["filler_material"].map(normalize_filler)
    df["preheat_c"] = pd.to_numeric(df.get("preheat_c"), errors="coerce")
    df["v_step_mm_s"] = pd.to_numeric(df["v_step_mm_s"], errors="coerce")
    df["l_star"] = pd.to_numeric(df["l_star"], errors="coerce").clip(0.0, 1.0)
    df["current_a"] = pd.to_numeric(df.get("current_a"), errors="coerce")
    df["condition_id"] = df.apply(lambda r: condition_id_from_values(r["base_material"], r["filler_material"], r.get("current_a"), r.get("preheat_c")), axis=1)
    return df.dropna(subset=["v_step_mm_s", "l_star"]).copy()


def load_processed_tmca(path: str | Path) -> pd.DataFrame:
    """Load the processed manuscript TMCA table."""
    df = pd.read_csv(path)
    if "base_material" not in df.columns:
        df["base_material"] = "Unknown"
    if "filler_material" not in df.columns:
        df["filler_material"] = "Autogenous"
    df["base_material"] = df["base_material"].map(normalize_material)
    df["filler_material"] = df["filler_material"].map(normalize_filler)
    df["current_a"] = pd.to_numeric(df.get("current_a"), errors="coerce")
    df["spacer_mm"] = pd.to_numeric(df.get("spacer_mm"), errors="coerce")
    df["v_step_mm_s"] = pd.to_numeric(df.get("v_step_mm_s"), errors="coerce")
    df["v_nc_mm_s"] = pd.to_numeric(df["v_nc_mm_s"], errors="coerce")
    if "load_increase_acceptance" not in df.columns:
        df["load_increase_acceptance"] = ""
    df["load_increase_acceptance"] = df["load_increase_acceptance"].fillna("").astype(str).str.lower().str.strip()
    df["condition_id"] = df.apply(lambda r: condition_id_from_values(r["base_material"], r["filler_material"], r.get("current_a"), r.get("preheat_c")), axis=1)
    return df.dropna(subset=["v_nc_mm_s"]).copy()


def write_csv(df: pd.DataFrame, path: str | Path) -> None:
    """Write a CSV file with parent-folder creation."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


# Backward-compatible aliases used by workflow scripts.
def load_manifest(path: str | Path) -> pd.DataFrame:
    return load_run_manifest(path)


def load_tmw_summary(path: str | Path) -> pd.DataFrame:
    return load_processed_tmw(path)


def load_tmca_summary(path: str | Path) -> pd.DataFrame:
    return load_processed_tmca(path)
