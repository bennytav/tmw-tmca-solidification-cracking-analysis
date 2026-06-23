# User-adjustable options

Most changes should be made in the **manifest** or in `config/default_analysis_config.json`, not by editing Python code.

---

## 1. Material and process condition

Use these manifest columns:

```text
condition_id
base_material
filler_material
current_a
preheat_c
spacer_mm
```

The code is material-agnostic.  Examples of valid `base_material` values:

```text
AA5083
AA6061
AA7075
304L
SS304L
Inconel718
Inconel 625
AZ31
```

The most important grouping variable is `condition_id`.  All rows with the same `condition_id` are summarized together.

---

## 2. Weld-start method

Use manifest column:

```text
weld_start_method
```

Allowed values:

```text
manifest                 use weld_start_time_s directly
manual_load_rise         use manual_load_rise_time_s + manual_load_to_start_delay_s
load_rise                automatic load-rise detection
fixed_time               use fixed_start_time_s
manifest_or_load_rise    use manifest value if present; otherwise use load rise
```

Recommended manual workflow:

```bash
python scripts/09_pick_weld_start.py --manifest data/manifest/my_tmca_manifest.csv --run-id RUN_ID --write-manifest
```

The plot allows zooming and repeated marker movement.  The selected value is saved only after the plot is closed.

---

## 3. Show or hide temperature

Per run, use manifest column:

```text
show_temperature
```

Allowed values:

```text
yes
no
auto
```

To show only selected thermocouples:

```text
temperature_columns = temperature_1_c,temperature_3_c
```

Global defaults are in:

```text
config/default_analysis_config.json
```

---

## 4. Crack-end coordinate used for TMCA V_NC

The default preference is in the configuration file:

```json
"crack_end_preference": ["l_surf_mm", "l_crack_mm", "l_ct_mm"]
```

This means:

1. use `l_surf_mm` if available;
2. otherwise use `l_crack_mm`;
3. otherwise use `l_ct_mm`.

To use CT first, change it to:

```json
"crack_end_preference": ["l_ct_mm", "l_surf_mm", "l_crack_mm"]
```

---

## 5. Include or exclude a run from summary

Use:

```text
include_in_summary
```

Accepted values:

```text
yes
no
```

The code still analyzes excluded runs and creates their single-run plots, but they are not used in TMCA or TMW summaries.

---

## 6. Force trimming and force smoothing

Global options are in:

```text
config/default_analysis_config.json
```

Useful settings:

```json
"trim_force_n": null,
"force_smooth_window_samples": 11,
"show_raw_force": true
```

Set `trim_force_n` only if a test should be plotted/processed only up to a specified force level.

---

## 7. Where to make Python-code changes

| Change | File | Function |
|---|---|---|
| Single-run plot appearance | `src/tmw_tmca_analysis/plots.py` | `plot_single_run_control()` |
| Weld-start logic | `src/tmw_tmca_analysis/run_analysis.py` | `determine_weld_start_time()` |
| Automatic load-rise threshold | `src/tmw_tmca_analysis/run_analysis.py` | `detect_load_rise_time()` |
| TMCA V_NC calculation | `src/tmw_tmca_analysis/run_analysis.py` | `analyze_one_run()` |
| TMW V_C--V_F fitting | `src/tmw_tmca_analysis/metrics.py` | `fit_tmw_transition()` |
| Summary figure style | `src/tmw_tmca_analysis/plots.py` | summary plot functions |
| Accepted input column names | `src/tmw_tmca_analysis/data_io.py` | `_CONTROL_ALIASES` |

More detail is in:

```text
docs/code_map_for_modification.md
```
