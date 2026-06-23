"""Plotting functions for TMW/TMCA analysis.

The plotting code is deliberately explicit: users can edit this file to change
single-run trace plots, TMCA box plots, TMW condition fits, and cross-condition
comparisons.
"""
from __future__ import annotations

from pathlib import Path
import hashlib
import re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch
from matplotlib.lines import Line2D

from .config import load_config, as_bool
from .metrics import piecewise_transition

DEFAULT_CURRENT_COLORS = {"160": "#E41A1C", "180": "#377EB8"}


def set_style() -> None:
    """Use a clean manuscript-style matplotlib configuration."""
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.labelsize": 12,
        "axes.titlesize": 15,
        "legend.fontsize": 9,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "axes.linewidth": 1.0,
        "savefig.dpi": 400,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
    })


def save_figure(fig: plt.Figure, path: str | Path) -> None:
    """Save a figure to the requested path with parent-folder creation."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight")


def _safe_name(value: object) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value)).strip("_") or "condition"


def _material_label(base: object) -> str:
    """Format a material name without assuming it is AA6061/AA7075."""
    s = str(base).strip()
    if not s or s.lower() in {"nan", "none", "unknown"}:
        return "Unknown"
    if re.fullmatch(r"[0-9]{4}", s):
        return f"AA{s}"
    return s


def _hash_color(value: object) -> str:
    """Deterministic fallback color for arbitrary materials/currents."""
    palette = list(plt.get_cmap("tab20").colors)
    digest = hashlib.md5(str(value).encode("utf-8")).hexdigest()
    idx = int(digest[:8], 16) % len(palette)
    rgb = palette[idx]
    return "#" + "".join(f"{int(round(c*255)):02x}" for c in rgb[:3])


def _base_color(base: object, config: dict | None = None) -> str:
    cfg = load_config(None) if config is None else config
    colors = cfg.get("styles", {}).get("material_colors", {})
    keys = [str(base).strip(), _material_label(base), str(base).strip().upper(), _material_label(base).upper()]
    for key in keys:
        if key in colors:
            return colors[key]
    return _hash_color(_material_label(base))


def _current_color(current: object, config: dict | None = None) -> str:
    cfg = load_config(None) if config is None else config
    colors = cfg.get("styles", {}).get("current_colors", DEFAULT_CURRENT_COLORS)
    try:
        key = str(int(round(float(current))))
    except Exception:
        key = str(current).strip()
    return colors.get(key, _hash_color(f"current_{key}"))


def _condition_label(row: pd.Series | dict, include_base: bool = True) -> str:
    get = row.get if hasattr(row, "get") else lambda key, default=None: default
    parts = []
    if include_base:
        parts.append(_material_label(get("base_material", "")))
    filler = str(get("filler_material", "")).strip()
    if filler:
        parts.append("Autogenous" if filler.lower() == "autogenous" else filler)
    try:
        preheat = float(get("preheat_c", np.nan))
        if np.isfinite(preheat):
            parts.append(f"{preheat:g} °C preheat")
    except Exception:
        pass
    return "\n".join([p for p in parts if p])


def _parse_temperature_columns(df: pd.DataFrame, requested: object) -> list[str]:
    """Choose temperature channels for plotting."""
    auto = [c for c in df.columns if c.lower().startswith("temperature_") and c.lower().endswith("_c")]
    if requested is None:
        return auto
    req = str(requested).strip()
    if not req or req.lower() in {"auto", "nan", "none"}:
        return auto
    cols = [c.strip() for c in re.split(r"[,;]", req) if c.strip()]
    return [c for c in cols if c in df.columns]


def _row_or_config_plot_temperature(metrics: dict, config: dict, df: pd.DataFrame) -> bool:
    row_value = str(metrics.get("show_temperature", "")).strip().lower()
    if row_value in {"yes", "true", "1", "on"}:
        return True
    if row_value in {"no", "false", "0", "off"}:
        return False
    setting = config.get("plotting", {}).get("show_temperature", "auto")
    if isinstance(setting, bool):
        return setting
    setting_s = str(setting).strip().lower()
    if setting_s in {"yes", "true", "1", "on"}:
        return True
    if setting_s in {"no", "false", "0", "off"}:
        return False
    return len(_parse_temperature_columns(df, metrics.get("temperature_columns") or config.get("plotting", {}).get("temperature_columns", "auto"))) > 0


def _smooth_series(values: pd.Series, window: object) -> pd.Series:
    try:
        win = int(float(window))
    except Exception:
        win = 1
    if win <= 1:
        return pd.to_numeric(values, errors="coerce")
    return pd.to_numeric(values, errors="coerce").rolling(win, center=True, min_periods=1).mean()


def plot_single_run_control(control: pd.DataFrame, metrics: dict, outpath: str | Path, config: dict | None = None) -> None:
    """Plot velocity, reaction force, and optional temperature for one weld.

    Change this function if you want a different single-test figure style.
    The most common user options are controlled from the manifest/config:
    ``show_temperature``, ``temperature_columns``, ``force_smooth_window_samples``,
    ``show_raw_force``, and the vertical-marker positions.
    """
    config = load_config(None) if config is None else config
    set_style()
    plot_cfg = config.get("plotting", {})
    df = control.sort_values("weld_length_mm").copy()
    x = df["weld_length_mm"].to_numpy(float)
    velocity = np.abs(pd.to_numeric(df["actuator_velocity_mm_s"], errors="coerce").to_numpy(float))
    force_raw = pd.to_numeric(df["reaction_force_n"], errors="coerce")
    force_smoothed = _smooth_series(force_raw, plot_cfg.get("force_smooth_window_samples", 11))

    fig, ax_v = plt.subplots(figsize=(8.4, 4.8))
    ax_v.plot(x, velocity, color="forestgreen", lw=1.3, label="Velocity")
    ax_v.set_xlabel("Weld length (mm)")
    ax_v.set_ylabel("Transverse velocity (mm/s)", color="forestgreen")
    ax_v.tick_params(axis="y", labelcolor="forestgreen")

    ax_f = ax_v.twinx()
    if as_bool(plot_cfg.get("show_raw_force", True), True):
        ax_f.plot(x, force_raw, color="red", lw=0.8, alpha=0.25, label="Reaction force, raw")
    ax_f.plot(x, force_smoothed, color="red", lw=1.2, alpha=0.9, label="Reaction force")
    ax_f.set_ylabel("Reaction force (N)", color="red")
    ax_f.tick_params(axis="y", labelcolor="red")

    if _row_or_config_plot_temperature(metrics, config, df):
        temp_cols = _parse_temperature_columns(df, metrics.get("temperature_columns") or plot_cfg.get("temperature_columns", "auto"))
        if temp_cols:
            ax_t = ax_v.twinx()
            ax_t.spines["right"].set_position(("axes", 1.12))
            colors = plt.get_cmap("tab10").colors
            mask = np.ones(len(df), dtype=bool)
            if as_bool(plot_cfg.get("temperature_during_weld_only", False), False):
                lweld = metrics.get("l_weld_mm", np.nan)
                try:
                    lweld = float(lweld)
                    if np.isfinite(lweld):
                        mask = (x >= 0) & (x <= lweld)
                except Exception:
                    pass
            for i, col in enumerate(temp_cols):
                y = _smooth_series(df[col], plot_cfg.get("temperature_smooth_window", 1))
                ax_t.plot(x[mask], y[mask], lw=1.0, color=colors[i % len(colors)], label=col.replace("temperature_", "T").replace("_c", ""))
            ax_t.set_ylabel("Temperature (°C)")

    markers = [
        ("speed_transition_weld_length_mm", r"change to $V_{\mathrm{step}}$", "deepskyblue", "-."),
        ("deceleration_start_weld_length_mm", r"start $a_{\mathrm{dec}}$", "darkorange", "-."),
        ("l_crack_mm", r"$L_{\mathrm{crack}}$", "limegreen", "--"),
        ("l_surf_mm", r"$L_{\mathrm{surf}}$", "darkgreen", ":"),
        ("l_ct_mm", r"$L_{\mathrm{CT}}$", "black", ":"),
        ("l_weld_mm", r"$L_{\mathrm{weld}}$", "magenta", "--"),
    ]
    for key, label, color, style in markers:
        try:
            value = float(metrics.get(key, np.nan))
        except Exception:
            value = np.nan
        if np.isfinite(value):
            ax_v.axvline(value, color=color, ls=style, lw=1.0, label=label)

    title = f"{metrics.get('run_id','')} | {metrics.get('protocol','')} | {_material_label(metrics.get('base_material',''))} {metrics.get('filler_material','')}"
    ax_v.set_title(title)
    try:
        vnc = float(metrics.get("v_nc_mm_s", np.nan))
    except Exception:
        vnc = np.nan
    if str(metrics.get("protocol", "")).upper() == "TMCA" and np.isfinite(vnc):
        ax_v.text(0.98, 0.06, rf"$V_{{\mathrm{{NC}}}}={vnc:.4f}$ mm/s", transform=ax_v.transAxes, ha="right", va="bottom", bbox=dict(facecolor="white", edgecolor="0.7", alpha=0.9))
    ax_v.grid(True, alpha=0.25)
    handles, labels = [], []
    for ax in fig.axes:
        h, l = ax.get_legend_handles_labels()
        handles.extend(h); labels.extend(l)
    # Keep unique labels while preserving order.
    unique = {}
    for h, l in zip(handles, labels):
        unique.setdefault(l, h)
    ax_v.legend(unique.values(), unique.keys(), loc="upper left", fontsize=8, frameon=True)
    fig.tight_layout()
    save_figure(fig, outpath)
    # Save a PDF copy from the same figure when requested. This avoids
    # recreating the plot a second time and keeps batch runs faster.
    try:
        if bool(config.get("plotting", {}).get("save_pdf", True)) and Path(outpath).suffix.lower() != ".pdf":
            save_figure(fig, Path(outpath).with_suffix(".pdf"))
    except Exception:
        pass
    plt.close(fig)


def plot_tmw_condition_fit(run_df: pd.DataFrame, fit_record: pd.Series | dict, outpath: str | Path, config: dict | None = None) -> None:
    """Plot L* versus V_step and the fitted V_C--V_F interval for one condition."""
    config = load_config(None) if config is None else config
    set_style()
    df = run_df.copy()
    df["v_step_mm_s"] = pd.to_numeric(df["v_step_mm_s"], errors="coerce")
    df["l_star"] = pd.to_numeric(df["l_star"], errors="coerce").clip(0, 1)
    df = df.dropna(subset=["v_step_mm_s", "l_star"]).sort_values("v_step_mm_s")
    if df.empty:
        raise ValueError("No finite V_step/L* data are available for plotting.")

    vc = float(fit_record["v_c_mm_s"])
    vf = float(fit_record["v_f_mm_s"])
    base = fit_record.get("base_material", df["base_material"].iloc[0])
    color = _base_color(base, config)
    xmin = max(0.0, min(float(df["v_step_mm_s"].min()), vc) - 0.010)
    xmax = max(float(df["v_step_mm_s"].max()), vf) + 0.010
    xs = np.linspace(xmin, xmax, 300)
    ys = piecewise_transition(xs, vc, vf)

    fig, ax = plt.subplots(figsize=(6.4, 4.8))
    ax.axvspan(xmin, vc, color="0.92", zorder=0)
    ax.axvspan(vc, vf, color=color, alpha=0.18, zorder=0, label=r"$V_C$--$V_F$ interval")
    ax.axvspan(vf, xmax, color="0.92", zorder=0)
    ax.plot(xs, ys, color=color, lw=2.0, label="transition fit")
    ax.scatter(df["v_step_mm_s"], df["l_star"], s=52, facecolors="white", edgecolors="black", linewidths=1.2, zorder=3, label="TMW welds")
    ax.axvline(vc, color="black", lw=1.1, ls="--")
    ax.axvline(vf, color="black", lw=1.1, ls="--")
    ax.text(vc, 0.04, rf"$V_C$={vc:.4f}", rotation=90, ha="right", va="bottom", fontsize=10)
    ax.text(vf, 0.96, rf"$V_F$={vf:.4f}", rotation=90, ha="left", va="top", fontsize=10)
    ax.text((xmin + vc) / 2, 0.53, "no crack", rotation=90, ha="center", va="center", color="0.25")
    ax.text((vf + xmax) / 2, 0.53, "full crack", rotation=90, ha="center", va="center", color="0.25")
    ax.set_xlabel(r"Selected constant velocity $V_{\mathrm{step}}$ (mm/s)")
    ax.set_ylabel(r"Normalized crack length $L^*$")
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(-0.05, 1.05)
    ax.grid(True, alpha=0.25)
    title = _condition_label(fit_record, True).replace("\n", ", ")
    current = fit_record.get("current_a", "")
    ax.set_title(f"TMW transition fit: {title}, {current:g} A" if isinstance(current, (int, float, np.floating)) and np.isfinite(current) else f"TMW transition fit: {title}")
    ax.legend(loc="lower right", fontsize=9, frameon=True)
    fig.tight_layout()
    save_figure(fig, outpath)
    plt.close(fig)


def plot_tmw_transition_summary(summary: pd.DataFrame, outpath: str | Path, config: dict | None = None) -> None:
    """Make a paper-style V_C--V_F comparison plot across conditions."""
    config = load_config(None) if config is None else config
    set_style()
    df = summary.copy().sort_values(["v_c_mm_s", "base_material", "filler_material"]).reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(7.0, 6.6))
    width = 0.32
    for i, row in df.iterrows():
        vc = float(row["v_c_mm_s"])
        vf = float(row["v_f_mm_s"])
        color = _base_color(row["base_material"], config)
        ax.add_patch(Rectangle((i - width / 2, vc), width, vf - vc, facecolor=color, edgecolor="black", linewidth=1.2, zorder=3))
        ax.text(i, vf + 0.0020, "fc", ha="center", va="bottom", fontsize=12)
        ax.text(i, vc - 0.0020, "nc", ha="center", va="top", fontsize=12)
        ax.text(i - width, (vc + vf) / 2, _condition_label(row, True), rotation=90, ha="center", va="center", fontsize=9)
    ymin = max(0.0, float(df["v_c_mm_s"].min()) - 0.012)
    ymax = float(df["v_f_mm_s"].max()) + 0.012
    ax.set_xlim(-0.75, len(df) - 0.25)
    ax.set_ylim(ymin, ymax)
    ax.set_xticks([])
    ax.set_ylabel(r"Transverse velocity $V$ (mm/s)")
    ax.set_title("Crack susceptibility ranking", pad=12)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.text(0.02, 0.96, "nc: no crack\nfc: full crack", transform=ax.transAxes, ha="left", va="top", fontsize=12)
    if len(df) >= 3:
        ax.annotate("Increasing $V$ level of transition range\nDecreasing crack susceptibility", xy=(len(df)-0.30, ymin+0.45*(ymax-ymin)), xytext=(1.20, ymin+0.18*(ymax-ymin)), arrowprops=dict(arrowstyle="-|>", lw=1.8, color="black"), rotation=30, ha="left", va="center", fontsize=11)
    handles = []
    for base in sorted(set(df["base_material"].astype(str)), key=str):
        handles.append(Patch(facecolor=_base_color(base, config), edgecolor="black", label=_material_label(base)))
    if handles:
        ax.legend(handles=handles, title="Base material", loc="lower right", frameon=False)
    fig.tight_layout()
    save_figure(fig, outpath)
    plt.close(fig)


def plot_tmca_vnc_summary(tmca_df: pd.DataFrame, outpath: str | Path, config: dict | None = None) -> None:
    """Make a paper-style TMCA box-and-whisker summary plot."""
    config = load_config(None) if config is None else config
    set_style()
    df = tmca_df.copy()
    if "preheat_c" not in df.columns:
        df["preheat_c"] = np.nan
    if "load_increase_acceptance" not in df.columns:
        df["load_increase_acceptance"] = ""
    df["v_nc_mm_s"] = pd.to_numeric(df["v_nc_mm_s"], errors="coerce")
    df = df.dropna(subset=["v_nc_mm_s", "base_material"]).copy()
    if df.empty:
        raise ValueError("No TMCA V_NC values are available for plotting.")
    if "current_a" not in df.columns:
        df["current_a"] = np.nan

    group_cols = ["condition_id", "base_material", "filler_material", "preheat_c", "current_a"]
    groups = []
    for keys, group in df.groupby(group_cols, dropna=False, sort=False):
        vals = group["v_nc_mm_s"].dropna().to_numpy(float)
        if vals.size:
            groups.append({"keys": keys, "rows": group, "values": vals, "mean": float(np.mean(vals))})
    groups = sorted(groups, key=lambda g: (str(g["keys"][1]), g["mean"]))

    positions = []
    xpos = 0.0
    previous_base = None
    for g in groups:
        base = str(g["keys"][1])
        if previous_base is not None and base != previous_base:
            xpos += 1.25
        positions.append(xpos)
        xpos += 1.0
        previous_base = base

    fig_width = max(8.0, min(16.0, 0.75 * len(groups) + 4.0))
    fig, ax = plt.subplots(figsize=(fig_width, 5.5))
    for pos, g in zip(positions, groups):
        condition_id, base, filler, preheat, current = g["keys"]
        vals = g["values"]
        color = _current_color(current, config)
        ax.boxplot(vals, positions=[pos], widths=0.45, patch_artist=True, showfliers=False, boxprops=dict(facecolor="0.92", edgecolor="black", linewidth=1.1), medianprops=dict(color=color, linewidth=2.0), whiskerprops=dict(color="black", linewidth=1.1), capprops=dict(color="black", linewidth=1.1))
        jitter = np.linspace(-0.10, 0.10, len(vals)) if len(vals) > 1 else np.array([0.0])
        ax.scatter(np.full(len(vals), pos) + jitter, vals, marker="s", s=44, facecolors="none", edgecolors=color, linewidths=1.2, zorder=3)
        rows = g["rows"].reset_index(drop=True)
        bad = rows["load_increase_acceptance"].astype(str).str.lower().eq("no").to_numpy()
        if bad.any():
            bad_vals = rows.loc[bad, "v_nc_mm_s"].to_numpy(float)
            ax.scatter(np.full(len(bad_vals), pos) + 0.12, bad_vals, marker="x", s=60, color=color, linewidths=1.4, zorder=4)
        label = _condition_label({"base_material": base, "filler_material": filler, "preheat_c": preheat}, False)
        if label:
            ax.text(pos + 0.35, float(np.mean(vals)), label, rotation=90, ha="left", va="center", fontsize=10)
    ax.set_ylabel(r"Crack-arrest velocity $V_{\mathrm{NC}}$ (mm/s)")
    ax.set_title(r"TMCA box-and-whisker summary (worst $\rightarrow$ best within each alloy)", pad=10)
    ax.grid(axis="y", linestyle="--", alpha=0.25)
    ax.set_xticks([])
    ymin = max(0.0, float(df["v_nc_mm_s"].min()) - 0.006)
    ymax = float(df["v_nc_mm_s"].max()) + 0.012
    ax.set_ylim(ymin, ymax)
    bases = [str(g["keys"][1]) for g in groups]
    pos_arr = np.asarray(positions)
    for base in sorted(set(bases), key=str):
        ps = pos_arr[[b == base for b in bases]]
        if ps.size:
            ax.text(float(ps.mean()), ymax - 0.004, _material_label(base), ha="center", va="top", fontsize=15, fontweight="bold")
    for base_left, base_right in zip(sorted(set(bases), key=str)[:-1], sorted(set(bases), key=str)[1:]):
        left_positions = [p for p, b in zip(positions, bases) if b == base_left]
        right_positions = [p for p, b in zip(positions, bases) if b == base_right]
        if left_positions and right_positions:
            sep = (max(left_positions) + min(right_positions)) / 2
            ax.axvspan(sep - 0.05, sep + 0.05, color="0.85", zorder=0)
            ax.axvline(sep, color="0.25", lw=1.4)
    current_values = [v for v in pd.to_numeric(df["current_a"], errors="coerce").dropna().unique()]
    handles = [Line2D([0], [0], marker="s", color=_current_color(v, config), markerfacecolor="none", lw=1.8, label=f"{int(round(v))} A") for v in sorted(current_values)]
    handles.append(Line2D([0], [0], marker="x", color="black", lw=0, label="post-transition load-increase\ncriterion not satisfied"))
    ax.legend(handles=handles, loc="upper left", frameon=True, framealpha=0.95)
    fig.tight_layout()
    save_figure(fig, outpath)
    plt.close(fig)


def condition_plot_filename(condition_id: object) -> str:
    return _safe_name(condition_id) + "_TMW_transition_fit.png"
