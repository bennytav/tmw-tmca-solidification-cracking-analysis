"""Import raw controller XML files into the standardized CSV format.

The public workflow uses **one standardized control CSV per weld**.  This
module converts the XML files exported by the TMW/TMCA control system into that
format.

Important design rule
---------------------
This module converts controller signals only.  It does **not** measure crack
lengths, decide if a run is valid, or calculate the final material/process
ranking.  Those decisions are stored in the manifest and in the run-analysis
stage, so users can check and correct each weld.
"""
from __future__ import annotations

from pathlib import Path
from io import BytesIO
import json
import math
import re
from typing import Iterable

import numpy as np
import pandas as pd
from lxml import etree

from .data_io import write_csv, text, to_float
from .schema import MANIFEST_RECOMMENDED

_DATA_TAGS = {"Current_Time", "MotorPos", "MotorVelo", "LoadCell"}


def _sanitize_xml_bytes(raw: bytes) -> bytes:
    """Remove illegal XML 1.0 control bytes from a raw XML export.

    Some controller exports may contain non-printable bytes.  Removing them
    makes the file readable by XML parsers without changing the numeric data.
    """
    delete = bytes(range(0x00, 0x09)) + b"\x0B\x0C" + bytes(range(0x0E, 0x20))
    identity = bytes.maketrans(b"", b"")
    return raw.translate(identity, delete)


def looks_like_controller_xml(path: str | Path) -> bool:
    """Return ``True`` when an XML file appears to be a controller time-series log.

    ``Parameters_*.xml`` files are skipped because they contain test settings,
    not time-series records.
    """
    path = Path(path)
    if path.name.lower().startswith("parameters"):
        return False
    try:
        sample = path.read_bytes()[:4096].decode("utf-8", errors="ignore")
    except Exception:
        return False
    return "<dataentry" in sample and all(tag in sample for tag in _DATA_TAGS)


def _safe_rel_stem(path: Path, root: Path) -> str:
    """Create a stable, unique run identifier from a relative XML path.

    Old controller folders sometimes reuse the same specimen/run name in
    different campaigns.  Using the relative folder path avoids overwriting
    single-run plots or metrics when duplicate file stems exist.
    """
    rel = path.relative_to(root).with_suffix("")
    return "__".join(rel.parts)


def read_controller_xml(path: str | Path) -> pd.DataFrame:
    """Read one raw controller XML file as a DataFrame with original channels.

    The function uses a streaming XML parser instead of ``pandas.read_xml``.
    This is much faster for the large controller logs and avoids loading a
    second full XML representation into memory.
    """
    path = Path(path)
    raw = _sanitize_xml_bytes(path.read_bytes())
    rows: list[dict[str, object]] = []
    tags = [
        "Current_Time", "MotorPos", "MotorVelo", "LoadCell",
        "Temper_1", "Temper_2", "Temper_3", "Temper_4",
    ]

    for _event, elem in etree.iterparse(BytesIO(raw), events=("end",), tag="value_1", recover=True):
        row: dict[str, object] = {}
        for tag in tags:
            child = elem.find(tag)
            row[tag] = child.text if child is not None else None
        rows.append(row)
        elem.clear()

    if not rows:
        raise ValueError(f"Controller XML {path} contains no time-series rows.")
    return pd.DataFrame(rows)


def controller_xml_to_standard_csv(path: str | Path) -> pd.DataFrame:
    """Convert one raw controller XML file into the standardized control CSV schema.

    Output columns are:

    - ``time_s``
    - ``actuator_position_mm``
    - ``actuator_velocity_mm_s``
    - ``reaction_force_n``
    - ``temperature_1_c`` ... ``temperature_4_c`` if present

    In the original controller files, ``Current_Time`` is stored in
    centiseconds, so ``time_s = Current_Time/100``.
    """
    raw = read_controller_xml(path)
    raw.columns = [str(c).strip() for c in raw.columns]

    def first_existing(candidates: Iterable[str]) -> str | None:
        for c in candidates:
            if c in raw.columns:
                return c
        return None

    time_col = first_existing(["Current_Time", "Time", "time", "Time_s"])
    pos_col = first_existing(["MotorPos", "Motor_Pos", "Position", "Pos", "MotorPosition"])
    vel_col = first_existing(["MotorVelo", "Velocity", "Motor_Velo", "MotorVelocity"])
    force_col = first_existing(["LoadCell", "Load", "ReactionForce", "Force"])

    missing = [name for name, col in [
        ("time", time_col), ("position", pos_col), ("velocity", vel_col), ("force", force_col)
    ] if col is None]
    if missing:
        raise ValueError(f"{path} is missing required controller channel(s): {missing}")

    out = pd.DataFrame()
    time_raw = pd.to_numeric(raw[time_col], errors="coerce")
    out["time_s"] = time_raw / 100.0 if time_col == "Current_Time" else time_raw
    out["actuator_position_mm"] = pd.to_numeric(raw[pos_col], errors="coerce")
    out["actuator_velocity_mm_s"] = pd.to_numeric(raw[vel_col], errors="coerce")
    out["reaction_force_n"] = pd.to_numeric(raw[force_col], errors="coerce")

    for i in range(1, 5):
        c = first_existing([f"Temper_{i}", f"Temperature_{i}", f"temperature_{i}_c", f"TC{i}"])
        if c is not None:
            out[f"temperature_{i}_c"] = pd.to_numeric(raw[c], errors="coerce")

    # Remove controller buffer/idle rows: all zeros or missing key values.
    out = out.dropna(subset=["time_s", "actuator_position_mm", "actuator_velocity_mm_s", "reaction_force_n"]).copy()
    nonzero = (
        (out["actuator_position_mm"].abs() > 0)
        | (out["actuator_velocity_mm_s"].abs() > 0)
        | (out["reaction_force_n"].abs() > 0)
    )
    out = out[nonzero].reset_index(drop=True)

    # Keep a stable time order and remove duplicated controller buffer rows.
    out = out.sort_values("time_s").drop_duplicates(
        subset=["time_s", "actuator_position_mm", "actuator_velocity_mm_s", "reaction_force_n"],
        keep="first",
    )
    return out.reset_index(drop=True)


def convert_xml_folder(input_dir: str | Path, output_dir: str | Path) -> pd.DataFrame:
    """Convert all controller XML files in a folder tree to standardized CSVs.

    The output folder preserves the raw-data subfolder structure.  This is
    important because duplicate specimen names can occur in different campaigns.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict] = []

    for xml in sorted(input_dir.rglob("*.xml")):
        if not looks_like_controller_xml(xml):
            continue

        rel = xml.relative_to(input_dir)
        out = output_dir / rel.with_suffix(".csv")
        out.parent.mkdir(parents=True, exist_ok=True)
        unique_run_id = _safe_rel_stem(xml, input_dir)

        try:
            df = controller_xml_to_standard_csv(xml)
            write_csv(df, out)
            records.append({
                "run_id": unique_run_id,
                "source_run_id": xml.stem,
                "raw_xml": str(xml),
                "control_csv": str(out),
                "n_rows": int(len(df)),
                "time_start_s": float(df["time_s"].min()) if len(df) else np.nan,
                "time_end_s": float(df["time_s"].max()) if len(df) else np.nan,
                "max_force_n": float(df["reaction_force_n"].max()) if len(df) else np.nan,
                "status": "converted",
                "message": "",
            })
        except Exception as exc:
            records.append({
                "run_id": unique_run_id,
                "source_run_id": xml.stem,
                "raw_xml": str(xml),
                "control_csv": "",
                "n_rows": 0,
                "time_start_s": np.nan,
                "time_end_s": np.nan,
                "max_force_n": np.nan,
                "status": "failed",
                "message": str(exc),
            })

    inventory = pd.DataFrame.from_records(records)
    write_csv(inventory, output_dir / "conversion_inventory.csv")
    return inventory


def _find_metric_json(metrics_dir: Path, run_id: str) -> Path | None:
    """Find an old ``*_metrics.json`` file using the original source run ID."""
    candidates = list(metrics_dir.rglob(f"{run_id}_metrics.json")) + list(metrics_dir.rglob(f"{run_id}.json"))
    return candidates[0] if candidates else None


def _load_metric_json(path: Path | None) -> dict:
    """Load one old metrics JSON file if it exists."""
    if path is None or not path.exists():
        return {}
    try:
        txt = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        txt = path.read_text(encoding="cp1255", errors="replace")
    try:
        # Python's JSON reader accepts NaN by default, which matches the old files.
        return json.loads(txt)
    except Exception:
        return {}


def make_manifest_scaffold(
    control_dir: str | Path,
    output_csv: str | Path,
    *,
    protocol: str,
    metrics_dir: str | Path | None = None,
) -> pd.DataFrame:
    """Make a manifest scaffold from standardized control CSVs.

    The scaffold is a starting point, not a final analysis table.  The user must
    still check/fill material information, weld settings, weld-start position,
    and crack measurements.  If matching ``*_metrics.json`` files are available,
    useful values from the previous analysis are copied as a starting point.
    """
    control_dir = Path(control_dir)
    metrics_base = Path(metrics_dir) if metrics_dir else None
    protocol = protocol.upper().strip()
    rows: list[dict] = []

    for csv_path in sorted(control_dir.rglob("*.csv")):
        if csv_path.name == "conversion_inventory.csv":
            continue

        # Use the relative CSV path so duplicate run names from different
        # campaign folders remain unique.
        run_id = "__".join(csv_path.relative_to(control_dir).with_suffix("").parts)
        source_run_id = csv_path.stem
        metric = _load_metric_json(_find_metric_json(metrics_base, source_run_id) if metrics_base else None)

        row = {c: "" for c in MANIFEST_RECOMMENDED}
        row.update({
            "run_id": run_id,
            "protocol": protocol,
            "control_csv": str(csv_path),
            "include_in_summary": "yes",
            "load_increase_acceptance": "",
            "notes": "fill missing metadata before analysis",
        })
        row["source_run_id"] = source_run_id

        if metric:
            row["v_high_mm_s"] = metric.get("V_initial_mm_s", "")
            decel = abs(to_float(metric.get("Deceleration_mm_s2")))
            row["a_dec_mm_s2"] = decel if math.isfinite(decel) else ""
            row["speed_transition_weld_length_mm"] = metric.get("Speed_Transition_mm", "")
            row["deceleration_start_weld_length_mm"] = metric.get("Speed_Transition_mm", "")
            row["l_weld_mm"] = metric.get("L_weld_mm", "")
            row["l_crack_mm"] = metric.get("L_crack_mm", "")
            row["l_surf_mm"] = metric.get("End_Crack_measured_mm", "")
            row["v_nc_mm_s"] = metric.get("Velocity_End_Crack_measured_mm_s", "")
            row["weld_travel_speed_mm_s"] = metric.get("Welding_Velocity_mm_s", "")
            row["notes"] = text(metric.get("Notes")) or row["notes"]

        rows.append(row)

    df = pd.DataFrame(rows)
    manual_cols = list(MANIFEST_RECOMMENDED) + ["source_run_id"]
    for c in manual_cols:
        if c not in df.columns:
            df[c] = ""
    df = df[manual_cols]
    write_csv(df, output_csv)
    return df
