# Re-analyzing TMCA/TMW raw data from folders

This document describes how to start from raw controller XML files and reproduce the TMW/TMCA analysis sequence.

## 1. Folder organization

Create private raw-data folders inside the repository folder, but do not commit them:

```text
raw_data/
  TMCA/
    <your TMCA campaign folders>
  TMW/
    <your TMW campaign folders>
```

The repository `.gitignore` excludes `raw_data/`.

## 2. Convert raw controller XML files

The analysis code does not read XML directly during the normal workflow.  It first converts each controller XML file to a standardized control CSV.

```bash
python scripts/07_convert_raw_xml_folder.py --input-dir raw_data/TMCA --output-dir data/control_csv/tmca_raw
python scripts/07_convert_raw_xml_folder.py --input-dir raw_data/TMW  --output-dir data/control_csv/tmw_raw
```

The standardized CSV columns are:

```text
time_s
actuator_position_mm
actuator_velocity_mm_s
reaction_force_n
temperature_1_c
temperature_2_c
temperature_3_c
temperature_4_c
```

Only the first four columns are required.  Temperature columns are included when present.

## 3. Create manifest scaffolds

```bash
python scripts/08_create_manifest_scaffold.py --control-dir data/control_csv/tmca_raw --protocol TMCA --metrics-dir raw_data/TMCA --output-csv data/manifest/my_tmca_manifest.csv
python scripts/08_create_manifest_scaffold.py --control-dir data/control_csv/tmw_raw  --protocol TMW  --output-csv data/manifest/my_tmw_manifest.csv
```

The TMCA scaffold can read matching `*_metrics.json` files to pre-fill `l_surf_mm`, `v_nc_mm_s`, `l_weld_mm`, and related values.  You must still check these values before using them.

## 4. Fill the manifest fields

For TMCA rows, fill/check:

```text
run_id
protocol = TMCA
control_csv
base_material
filler_material
current_a
preheat_c, if used
spacer_mm
v_high_mm_s
v_step_mm_s
a_dec_mm_s2
weld_start_time_s
weld_travel_speed_mm_s
speed_transition_weld_length_mm
deceleration_start_weld_length_mm
l_weld_mm
l_surf_mm or l_crack_mm
v_nc_mm_s, optional; calculated from the trace if blank
load_increase_acceptance = yes/no
include_in_summary = yes/no
```

For TMW rows, fill/check:

```text
run_id
protocol = TMW
control_csv
base_material
filler_material
current_a
preheat_c, if used
spacer_mm
v_high_mm_s
v_step_mm_s
weld_start_time_s
weld_travel_speed_mm_s
speed_transition_weld_length_mm
l_weld_mm
l_crack_mm
l_star, optional; calculated as l_crack_mm/l_weld_mm if blank
crack_state, optional; calculated from L* if blank
include_in_summary = yes/no
```

## 5. Analyze TMCA first

```bash
python scripts/01_analyze_tmca_screening.py --manifest data/manifest/my_tmca_manifest.csv
```

Inspect every plot in:

```text
outputs/01_tmca_run_analysis/run_plots/
```

Then summarize:

```bash
python scripts/02_summarize_tmca_screening.py
python scripts/03_plan_tmw_from_tmca.py
```

## 6. Analyze TMW bracketing

Use the TMCA result only as the first estimate for TMW `V_step` values.  Add lower and higher TMW speeds until no-crack and full-crack endpoints are bracketed.

```bash
python scripts/04_analyze_tmw_bracketing.py --manifest data/manifest/my_tmw_manifest.csv
```

Inspect every plot in:

```text
outputs/04_tmw_run_analysis/run_plots/
```

Fit each condition:

```bash
python scripts/05_fit_tmw_conditions.py
```

Inspect the condition plots in:

```text
outputs/05_tmw_condition_fits/condition_transition_plots/
```

Compare all fitted conditions:

```bash
python scripts/06_compare_tmw_conditions.py
```

## 7. Where to edit code

- Single-test plot appearance: `src/tmw_tmca_analysis/plots.py`, function `plot_single_run_control()`.
- Single-test metric extraction: `src/tmw_tmca_analysis/run_analysis.py`, function `analyze_one_run()`.
- TMW transition fitting: `src/tmw_tmca_analysis/metrics.py`, function `fit_tmw_transition()`.
- TMCA summary statistics: `src/tmw_tmca_analysis/metrics.py`, function `summarize_tmca_vnc()`.
- Summary figure appearance: `src/tmw_tmca_analysis/plots.py`, functions `plot_tmca_vnc_summary()` and `plot_tmw_transition_summary()`.
- Input column definitions: `src/tmw_tmca_analysis/schema.py`.
