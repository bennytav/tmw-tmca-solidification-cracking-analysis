"""Configuration helpers for the TMW/TMCA analysis workflow.

The public package is intended for future tests, not only the manuscript data.
Most analysis choices are therefore read from a JSON configuration file and can
also be overridden in the run manifest.  The default configuration is stored in
``config/default_analysis_config.json``.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import json
from typing import Any, Mapping

DEFAULT_CONFIG: dict[str, Any] = {
    "analysis": {
        "default_weld_travel_speed_mm_s": None,
        "crack_end_preference": ["l_surf_mm", "l_crack_mm", "l_ct_mm"],
        "trim_force_n": None,
        "max_force_n": None,
        "no_crack_lstar_threshold": 0.02,
        "full_crack_lstar_threshold": 0.98,
    },
    "start_detection": {
        "default_method": "manifest_or_load_rise",
        "load_rise_delta_n": 2.0,
        "baseline_window_s": 2.0,
        "auto_load_to_start_delay_s": 0.0,
        "manual_load_to_start_delay_s": 3.0,
        "fixed_start_time_s": None,
    },
    "plotting": {
        "show_temperature": "auto",
        "temperature_columns": "auto",
        "temperature_during_weld_only": False,
        "temperature_smooth_window": 1,
        "show_raw_force": True,
        "force_smooth_window_samples": 11,
        "force_smooth_method": "rolling",
        "save_pdf": True,
        "show_stress": False,
        "sheet_thickness_mm": None,
        "k_factor": 0.707,
        "style": "manuscript",
    },
    "styles": {
        "material_colors": {
            "AA6061": "#5B8CCB", "6061": "#5B8CCB",
            "AA7075": "#E6862F", "7075": "#E6862F",
            "AA5083": "#4DAF4A", "5083": "#4DAF4A",
            "304L": "#984EA3", "SS304L": "#984EA3",
            "INCONEL": "#A65628", "INCONEL718": "#A65628",
        },
        "current_colors": {"160": "#E41A1C", "180": "#377EB8"},
    },
}


def deep_update(base: dict[str, Any], update: Mapping[str, Any]) -> dict[str, Any]:
    """Recursively update ``base`` with ``update`` and return ``base``."""
    for key, value in update.items():
        if isinstance(value, Mapping) and isinstance(base.get(key), dict):
            deep_update(base[key], value)
        else:
            base[key] = value
    return base


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load a JSON configuration file and merge it with defaults.

    Parameters
    ----------
    path:
        Path to a JSON file.  If ``None`` or if the file does not exist, the
        package defaults are used.
    """
    cfg = deepcopy(DEFAULT_CONFIG)
    if path is None:
        return cfg
    path = Path(path)
    if not path.exists():
        return cfg
    with path.open("r", encoding="utf-8") as f:
        user = json.load(f)
    if not isinstance(user, dict):
        raise ValueError(f"Configuration file must contain a JSON object: {path}")
    return deep_update(cfg, user)


def row_value(row: Any, key: str, default: Any = None) -> Any:
    """Read a value from a pandas Series/dict while treating blanks as missing."""
    try:
        value = row.get(key, default)
    except Exception:
        return default
    if value is None:
        return default
    try:
        import pandas as pd
        if pd.isna(value):
            return default
    except Exception:
        pass
    if isinstance(value, str) and value.strip() == "":
        return default
    return value


def as_bool(value: Any, default: bool = False) -> bool:
    """Parse common yes/no strings."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"yes", "y", "true", "1", "on"}:
        return True
    if text in {"no", "n", "false", "0", "off"}:
        return False
    return default
