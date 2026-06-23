# Code map: where to make changes

This repository is organized so most users only edit the manifest and configuration.  If you need to change the analysis behavior, use this map.

## Scripts folder

The `scripts/` folder contains user-facing commands.  These scripts should remain short.  They load arguments and call functions from `src/tmw_tmca_analysis/`.

| Script | Purpose |
|---|---|
| `00_show_workflow.py` | Prints the complete workflow. |
| `01_analyze_tmca_screening.py` | Analyzes each TMCA run and creates one plot per run. |
| `02_summarize_tmca_screening.py` | Summarizes TMCA `V_NC` results. |
| `03_plan_tmw_from_tmca.py` | Suggests initial TMW `V_step` values from TMCA results. |
| `04_analyze_tmw_bracketing.py` | Analyzes each TMW run and creates one plot per run. |
| `05_fit_tmw_conditions.py` | Fits `V_C--V_F` for each TMW condition. |
| `06_compare_tmw_conditions.py` | Compares fitted conditions in one summary plot. |
| `07_convert_raw_xml_folder.py` | Converts raw controller XML files to standardized CSV. |
| `08_create_manifest_scaffold.py` | Builds a manifest scaffold from control CSV files. |
| `09_pick_weld_start.py` | Interactive manual load-rise/weld-start picker. |

## Source-code folder

| File | Main role | Change this when... |
|---|---|---|
| `data_io.py` | Loads CSV/manifest files and normalizes labels. | You need to accept new column names or new label normalization. |
| `schema.py` | Defines expected columns. | You want to add a new manifest/control column. |
| `run_analysis.py` | Converts one manifest row into run metrics. | You want to change `L*`, `V_NC`, crack-end selection, or weld-start logic. |
| `weld_start.py` | Utility functions for weld-start detection. | You want to change automatic threshold behavior. |
| `metrics.py` | Campaign-level metrics. | You want to change TMCA summaries or TMW transition fitting. |
| `plots.py` | All plot styles. | You want to change fonts, colors, labels, markers, or output size. |
| `raw_import.py` | Converts raw XML logs to control CSV. | You want to support a different raw controller file format. |
| `workflow.py` | Connects scripts to source functions. | You want to change the order of outputs or file names. |

## Most common edits

### Show temperature in single-run plots

Option 1, in the manifest:

```text
show_temperature = yes
temperature_columns = temperature_1_c,temperature_2_c
```

Option 2, globally in `config/default_analysis_config.json`:

```json
"show_temperature": true
```

### Change vertical markers in single-run plots

Edit this list in `src/tmw_tmca_analysis/plots.py` inside `plot_single_run_control()`:

```python
markers = [
    ("speed_transition_weld_length_mm", "change to V_step", ...),
    ("deceleration_start_weld_length_mm", "start a_dec", ...),
    ("l_crack_mm", "L_crack", ...),
    ...
]
```

### Use CT crack end instead of surface crack end for TMCA

Change `crack_end_preference` in `config/default_analysis_config.json`:

```json
"crack_end_preference": ["l_ct_mm", "l_surf_mm", "l_crack_mm"]
```

### Add a new material color

Edit `styles.material_colors` in `config/default_analysis_config.json`:

```json
"AA5083": "#4DAF4A",
"304L": "#984EA3",
"INCONEL718": "#A65628"
```

If no color is provided, the code assigns a deterministic fallback color.
