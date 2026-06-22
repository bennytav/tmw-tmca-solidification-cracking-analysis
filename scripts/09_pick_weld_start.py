"""Step 09: manually choose the load-rise point used to define weld start.

Why this script exists
----------------------
The weld-length coordinate is calculated from the weld-start time.  In many
TMW/TMCA runs the most reliable practical reference is the first clear increase
in the load-cell signal.  This script lets the user choose that load-rise point
manually from the force trace, then writes the result back to the manifest.

Important behavior
------------------
The selected point is NOT saved immediately after the first mouse click.
Instead:

1. A plot opens for the selected run.
2. The user can zoom/pan using the Matplotlib toolbar.
3. The user can left-click multiple times; each click moves the selected line.
4. The user can right-click to clear the selected point.
5. The selected point is accepted only after the figure window is closed.
6. By default, the terminal asks for confirmation after the window closes.

This makes it possible to enlarge the load-rise region, adjust the selected
point, and only then save the selected value.

Typical command
---------------
    python scripts/09_pick_weld_start.py \
        --manifest data/manifest/my_tmca_manifest.csv \
        --run-id RUN_ID \
        --write-manifest

For TMW, use the same script with the TMW manifest:

    python scripts/09_pick_weld_start.py \
        --manifest data/manifest/my_tmw_manifest.csv \
        --run-id RUN_ID \
        --write-manifest

Non-interactive command, useful when the correct time is already known:

    python scripts/09_pick_weld_start.py \
        --manifest data/manifest/my_tmca_manifest.csv \
        --run-id RUN_ID \
        --load-rise-time-s 12.345 \
        --write-manifest
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from _bootstrap import bootstrap
ROOT = bootstrap(__file__)

from tmw_tmca_analysis.data_io import load_control_csv, load_run_manifest, write_csv, text, to_float
from tmw_tmca_analysis.config import load_config


@dataclass
class ManualPickResult:
    """Result returned by the interactive selector.

    Attributes
    ----------
    load_rise_time_s:
        User-selected load-rise time in seconds.  NaN means no valid point was
        selected or the point was cleared before closing the plot.
    changed:
        True when the user moved/cleared the marker during the session.
    """

    load_rise_time_s: float
    changed: bool


def resolve_control_path(control_csv: object, *, manifest_path: Path, repo_root: Path) -> Path:
    """Resolve the control CSV path from one manifest row.

    The manifest can contain either:
    - an absolute path; or
    - a path relative to the manifest folder; or
    - a path relative to the repository root.
    """
    p = Path(text(control_csv))
    if p.is_absolute():
        return p
    by_manifest = manifest_path.resolve().parent / p
    if by_manifest.exists():
        return by_manifest
    by_repo = repo_root.resolve() / p
    if by_repo.exists():
        return by_repo
    # Return the manifest-relative path because it gives a useful error message
    # later if the file is missing.
    return by_manifest


def _safe_force_baseline(t: np.ndarray, f: np.ndarray, baseline_s: float) -> tuple[float, float]:
    """Return baseline force and threshold-guide time window.

    This threshold is only drawn as a guide.  The manual pick is controlled by
    the user, not by the automatic threshold.
    """
    finite = np.isfinite(t) & np.isfinite(f)
    if not np.any(finite):
        return np.nan, np.nan
    t0 = float(np.nanmin(t[finite]))
    base_mask = finite & (t <= t0 + float(baseline_s))
    if not np.any(base_mask):
        base_mask = finite & (np.arange(len(t)) < min(10, len(t)))
    baseline = float(np.nanmean(f[base_mask])) if np.any(base_mask) else np.nan
    return baseline, t0


def _toolbar_is_active(fig: plt.Figure) -> bool:
    """Return True while Matplotlib zoom/pan mode is active.

    When the toolbar is in zoom/pan mode, mouse clicks should control the zoom or
    pan operation, not move the weld-start marker.
    """
    manager = getattr(fig.canvas, "manager", None)
    toolbar = getattr(manager, "toolbar", None)
    mode = getattr(toolbar, "mode", "") if toolbar is not None else ""
    return bool(str(mode))


def pick_one_interactive(
    control: pd.DataFrame,
    title: str,
    *,
    baseline_s: float,
    delta_n: float,
    delay_s: float,
    initial_load_rise_time_s: float = np.nan,
) -> ManualPickResult:
    """Open a zoomable plot and return the final selected load-rise time.

    How to use the plot
    -------------------
    - Use the toolbar magnifying glass or pan button to zoom/move the view.
    - Left-click the force trace to set or move the selected load-rise line.
    - Right-click to clear the selected line.
    - Press the left/right arrow keys for fine adjustment after selecting.
    - Press ``r`` to reset the zoom.
    - Press ``c`` to clear the selection.
    - Press ``enter`` or simply close the window to accept the current marker.

    The function does not write any file.  The caller writes the manifest after
    the figure is closed and the selected value is confirmed.
    """
    t = control["time_s"].to_numpy(float)
    f = control["reaction_force_n"].to_numpy(float)
    v = np.abs(control["actuator_velocity_mm_s"].to_numpy(float))

    baseline, t0 = _safe_force_baseline(t, f, baseline_s)
    threshold = baseline + float(delta_n) if np.isfinite(baseline) else np.nan

    # A best-effort automatic load-rise line is drawn as a visual guide only.
    auto_time = np.nan
    if np.isfinite(threshold):
        candidates = np.where(f > threshold)[0]
        if candidates.size:
            auto_time = float(t[candidates[0]])

    fig, ax_f = plt.subplots(figsize=(12, 6))
    ax_f.plot(t, f, color="red", lw=1.1, label="reaction force")
    if np.isfinite(threshold):
        ax_f.axhline(threshold, color="red", ls="--", lw=0.9, alpha=0.45, label="threshold guide")
    if np.isfinite(auto_time):
        ax_f.axvline(auto_time, color="0.55", ls=":", lw=1.0, label="automatic guide")
    ax_f.set_xlabel("Time (s)")
    ax_f.set_ylabel("Reaction force (N)", color="red")
    ax_f.tick_params(axis="y", labelcolor="red")
    ax_f.grid(True, alpha=0.25)

    ax_v = ax_f.twinx()
    ax_v.plot(t, v, color="forestgreen", lw=0.9, alpha=0.75, label="absolute velocity")
    ax_v.set_ylabel("Transverse velocity (mm/s)", color="forestgreen")
    ax_v.tick_params(axis="y", labelcolor="forestgreen")

    selected_time = [float(initial_load_rise_time_s) if np.isfinite(initial_load_rise_time_s) else np.nan]
    changed = [False]
    selected_line = [None]
    info_text = [None]
    xlim0 = ax_f.get_xlim()
    ylim0 = ax_f.get_ylim()

    def update_marker(new_time: float | None) -> None:
        """Move or remove the selected-load-rise marker."""
        if new_time is None or not np.isfinite(new_time):
            selected_time[0] = np.nan
        else:
            selected_time[0] = float(new_time)

        # Remove old marker and old text box.
        if selected_line[0] is not None:
            selected_line[0].remove()
            selected_line[0] = None
        if info_text[0] is not None:
            info_text[0].remove()
            info_text[0] = None

        if np.isfinite(selected_time[0]):
            selected_line[0] = ax_f.axvline(selected_time[0], color="black", ls="-", lw=1.8, label="selected load rise")
            weld_start = selected_time[0] + float(delay_s)
            info_text[0] = ax_f.text(
                0.02, 0.96,
                f"Selected load rise: {selected_time[0]:.4f} s\nWeld start = load rise + {delay_s:g} s = {weld_start:.4f} s",
                transform=ax_f.transAxes,
                ha="left", va="top",
                bbox=dict(facecolor="white", edgecolor="black", alpha=0.90),
                fontsize=10,
            )
        fig.canvas.draw_idle()

    def on_click(event) -> None:
        """Mouse handler: left-click moves marker, right-click clears it."""
        if event.inaxes not in {ax_f, ax_v}:
            return
        if _toolbar_is_active(fig):
            return
        if event.button == 1 and event.xdata is not None:
            update_marker(float(event.xdata))
            changed[0] = True
        elif event.button == 3:
            update_marker(np.nan)
            changed[0] = True

    def on_key(event) -> None:
        """Keyboard handler for fine adjustment and closing."""
        key = str(event.key).lower() if event.key is not None else ""
        if key in {"enter", "return"}:
            plt.close(fig)
            return
        if key in {"escape", "q"}:
            # Clear before closing when the user explicitly cancels.
            update_marker(np.nan)
            changed[0] = True
            plt.close(fig)
            return
        if key == "c":
            update_marker(np.nan)
            changed[0] = True
            return
        if key == "r":
            ax_f.set_xlim(xlim0)
            ax_f.set_ylim(ylim0)
            fig.canvas.draw_idle()
            return
        if key in {"left", "right"} and np.isfinite(selected_time[0]):
            # Step size is 0.1% of the current x-range.  This gives fine control
            # after zooming in.
            x0, x1 = ax_f.get_xlim()
            step = abs(x1 - x0) * 0.001
            if event.key == "left":
                step *= -1
            update_marker(selected_time[0] + step)
            changed[0] = True

    # Draw an existing value, if the manifest already contains one.
    update_marker(selected_time[0])

    # Put a compact instruction block in the title so first-time users know what
    # to do without opening the documentation.
    fig.suptitle(
        title
        + "\nLeft-click: set/move load-rise line | right-click or c: clear | toolbar: zoom/pan | Enter/close: accept",
        fontsize=12,
    )

    # Build one combined legend from both axes.
    handles, labels = [], []
    for ax in (ax_f, ax_v):
        h, l = ax.get_legend_handles_labels()
        handles.extend(h)
        labels.extend(l)
    unique = {}
    for h, l in zip(handles, labels):
        unique.setdefault(l, h)
    ax_f.legend(unique.values(), unique.keys(), loc="lower right", fontsize=9, frameon=True)

    fig.canvas.mpl_connect("button_press_event", on_click)
    fig.canvas.mpl_connect("key_press_event", on_key)
    fig.tight_layout()
    plt.show(block=True)

    return ManualPickResult(load_rise_time_s=float(selected_time[0]), changed=bool(changed[0]))


def _ask_yes_no_repick(prompt: str) -> str:
    """Ask the user to confirm the selected value after the plot closes."""
    while True:
        ans = input(prompt).strip().lower()
        if ans in {"", "y", "yes"}:
            return "yes"
        if ans in {"n", "no"}:
            return "no"
        if ans in {"r", "reopen", "repick"}:
            return "repick"
        print("Type y, n, or r.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pick load-rise times manually and write weld-start values to a manifest.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--manifest", type=Path, default=ROOT / "data" / "manifest" / "run_manifest_template.csv",
                        help="Manifest CSV to read. Usually my_tmca_manifest.csv or my_tmw_manifest.csv.")
    parser.add_argument("--output-manifest", type=Path, default=None,
                        help="Manifest CSV to write. Default: <manifest stem>_manual_start.csv.")
    parser.add_argument("--config", type=Path, default=ROOT / "config" / "default_analysis_config.json",
                        help="Analysis-configuration JSON file.")
    parser.add_argument("--run-id", type=str, default=None,
                        help="Pick only this run_id. Recommended for first-time use.")
    parser.add_argument("--protocol", type=str, default=None, choices=["TMCA", "TMW", "tmca", "tmw"],
                        help="Pick only rows from one protocol.")
    parser.add_argument("--delay-s", type=float, default=None,
                        help="Delay added to the selected load-rise time to define weld_start_time_s.")
    parser.add_argument("--baseline-s", type=float, default=None,
                        help="Early-time baseline window used only for the threshold guide line.")
    parser.add_argument("--delta-n", type=float, default=None,
                        help="Force increase used only for the threshold guide line.")
    parser.add_argument("--load-rise-time-s", type=float, default=None,
                        help="Non-interactive mode: use this load-rise time instead of opening a plot.")
    parser.add_argument("--write-manifest", action="store_true",
                        help="Overwrite the input manifest. Without this, a new *_manual_start.csv file is written.")
    parser.add_argument("--no-confirm", action="store_true",
                        help="Do not ask for terminal confirmation after each figure closes.")
    args = parser.parse_args()

    cfg = load_config(args.config)
    start_cfg = cfg.get("start_detection", {})
    delay = args.delay_s if args.delay_s is not None else float(start_cfg.get("manual_load_to_start_delay_s", 3.0))
    baseline_s = args.baseline_s if args.baseline_s is not None else float(start_cfg.get("baseline_window_s", 2.0))
    delta_n = args.delta_n if args.delta_n is not None else float(start_cfg.get("load_rise_delta_n", 2.0))

    manifest = load_run_manifest(args.manifest)
    # These columns may be entirely blank in a new CSV, so pandas can infer a
    # numeric dtype.  Cast them to object/string-compatible dtype before writing
    # text values such as "manual_load_rise".
    for col in ["weld_start_method"]:
        if col in manifest.columns:
            manifest[col] = manifest[col].astype("object")
    selected = pd.Series(True, index=manifest.index)
    if args.run_id:
        selected &= manifest["run_id"].astype(str).eq(args.run_id)
    if args.protocol:
        selected &= manifest["protocol"].astype(str).str.upper().eq(args.protocol.upper())
    if not selected.any():
        raise SystemExit("No manifest rows matched the requested run-id/protocol.")
    if args.load_rise_time_s is not None and selected.sum() > 1 and not args.run_id:
        raise SystemExit("--load-rise-time-s was supplied for more than one row. Add --run-id or select interactively.")

    for idx, row in manifest[selected].iterrows():
        run_id = text(row.get("run_id")) or f"row_{idx}"
        control_path = resolve_control_path(row["control_csv"], manifest_path=args.manifest, repo_root=ROOT)
        control = load_control_csv(control_path)
        title = f"{run_id} | {row['protocol']} | {row.get('base_material','')} {row.get('filler_material','')}"

        while True:
            if args.load_rise_time_s is not None:
                picked = ManualPickResult(float(args.load_rise_time_s), changed=True)
            else:
                picked = pick_one_interactive(
                    control,
                    title,
                    baseline_s=baseline_s,
                    delta_n=delta_n,
                    delay_s=delay,
                    initial_load_rise_time_s=to_float(row.get("manual_load_rise_time_s")),
                )

            if not np.isfinite(picked.load_rise_time_s):
                print(f"{run_id}: no load-rise point selected; row unchanged.")
                break

            weld_start = picked.load_rise_time_s + delay
            print(f"{run_id}: selected load rise = {picked.load_rise_time_s:.4f} s; weld start = {weld_start:.4f} s")
            if args.no_confirm or args.load_rise_time_s is not None:
                decision = "yes"
            else:
                decision = _ask_yes_no_repick("Save this value? [Y=yes / n=no / r=reopen plot] ")
            if decision == "repick":
                continue
            if decision == "no":
                print(f"{run_id}: selection was not saved; row unchanged.")
                break

            # Only now, after the figure is closed and the user has accepted the
            # value, update the manifest table.
            manifest.loc[idx, "weld_start_method"] = "manual_load_rise"
            manifest.loc[idx, "manual_load_rise_time_s"] = picked.load_rise_time_s
            manifest.loc[idx, "manual_load_to_start_delay_s"] = delay
            manifest.loc[idx, "weld_start_time_s"] = weld_start
            break

    out = args.manifest if args.write_manifest else (args.output_manifest or args.manifest.with_name(args.manifest.stem + "_manual_start.csv"))
    write_csv(manifest, out)
    print(f"Wrote updated manifest: {out}")
    print("Next step: run the TMCA/TMW analysis with this manifest.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled by user.", file=sys.stderr)
        raise SystemExit(130)
