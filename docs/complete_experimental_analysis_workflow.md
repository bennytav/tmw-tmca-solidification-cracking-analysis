# Complete experimental and analysis workflow

This document describes the intended use of the code for a new user.  The code is not limited to the manuscript dataset.  It can be used for any material/filler/current condition if the manifest is filled correctly.

---

## Core principle

The workflow has two levels:

1. **Single-run analysis:** inspect one weld at a time.
2. **Campaign summary:** summarize only accepted runs after the single-run plots have been checked.

A summary figure is only meaningful if the individual run plots are correct.

---

# Part A: TMCA fast screening

## A1. Perform TMCA tests

TMCA uses:

```text
V_high -> V_step -> constant deceleration a_dec
```

The purpose is to perform a fast screening run and estimate a crack-arrest velocity metric, `V_NC`.  `V_NC` is not assumed to be identical to the constant-velocity TMW `V_C`; it is used to plan the next TMW tests.

## A2. Export one controller CSV per TMCA weld

Each weld must have a separate CSV file.  Minimum columns:

```text
time_s
actuator_position_mm
actuator_velocity_mm_s
reaction_force_n
```

Recommended temperature columns:

```text
temperature_1_c
temperature_2_c
temperature_3_c
temperature_4_c
```

If the control system exports XML files, convert them first:

```bash
python scripts/07_convert_raw_xml_folder.py --input-dir raw_data/TMCA --output-dir data/control_csv/tmca_raw
```

## A3. Create or fill the TMCA manifest

Create a scaffold:

```bash
python scripts/08_create_manifest_scaffold.py --control-dir data/control_csv/tmca_raw --protocol TMCA --metrics-dir raw_data/TMCA --output-csv data/manifest/my_tmca_manifest.csv
```

Then open the CSV and fill/check:

```text
run_id
control_csv
condition_id
base_material
filler_material
current_a
v_high_mm_s
v_step_mm_s
a_dec_mm_s2
weld_travel_speed_mm_s
l_surf_mm or l_ct_mm
include_in_summary
```

Use a consistent `condition_id`.  All rows with the same `condition_id` are summarized together.

Examples:

```text
AA5083_ER5356_160A
304L_Autogenous_120A
Inconel718_ERNiCr_90A
AA7075_7075TiC_180A
```

## A4. Select or confirm weld start

If `weld_length_mm` is not already in the control CSV, the analysis must know where the weld starts.  The usual manual method is to select the load-rise point in the force trace.

```bash
python scripts/09_pick_weld_start.py --manifest data/manifest/my_tmca_manifest.csv --run-id RUN_ID --write-manifest
```

The plot lets the user zoom/pan, click several times, and save the final selected value only after closing the figure.

## A5. Analyze each TMCA run

```bash
python scripts/01_analyze_tmca_screening.py --manifest data/manifest/my_tmca_manifest.csv
```

Check:

```text
outputs/01_tmca_run_analysis/run_plots/
outputs/01_tmca_run_analysis/tmca_run_metrics.csv
```

For each plot, verify:

- the high-speed initiation segment is correct;
- the transition to `V_step` is visible;
- the deceleration region is correct;
- `L_surf`, `L_CT`, or the selected crack end is positioned correctly;
- the force trace is reasonable;
- optional temperature curves appear only if requested.

## A6. Summarize TMCA screening

After accepting the single-run plots:

```bash
python scripts/02_summarize_tmca_screening.py
```

Outputs:

```text
outputs/02_tmca_screening_summary/tmca_screening_summary.csv
outputs/02_tmca_screening_summary/TMCA_transition_range_TMWstyle_box.png
outputs/02_tmca_screening_summary/recommended_tmw_vstep_plan.csv
```

## A7. Plan first TMW V_step values from TMCA

```bash
python scripts/03_plan_tmw_from_tmca.py
```

Use the output only as an initial plan.  If the first TMW tests do not bracket no-crack and full-crack cases, add lower or higher `V_step` values.

---

# Part B: Constant-velocity TMW bracketing

## B1. Perform TMW tests

TMW uses:

```text
V_high -> constant V_step
```

For each material/filler/current/thermal condition, perform several welds at different `V_step` values.  The objective is to bracket the transition from no visible crack propagation to full crack propagation.

## B2. Export one controller CSV per TMW weld

If the control system exports XML files, convert them:

```bash
python scripts/07_convert_raw_xml_folder.py --input-dir raw_data/TMW --output-dir data/control_csv/tmw_raw
```

## B3. Create or fill the TMW manifest

```bash
python scripts/08_create_manifest_scaffold.py --control-dir data/control_csv/tmw_raw --protocol TMW --output-csv data/manifest/my_tmw_manifest.csv
```

Fill/check:

```text
run_id
control_csv
condition_id
base_material
filler_material
current_a
v_high_mm_s
v_step_mm_s
weld_travel_speed_mm_s
l_weld_mm
l_crack_mm
include_in_summary
```

If `l_star` is blank, the code calculates:

```text
l_star = l_crack_mm / l_weld_mm
```

## B4. Select or confirm weld start

```bash
python scripts/09_pick_weld_start.py --manifest data/manifest/my_tmw_manifest.csv --run-id RUN_ID --write-manifest
```

## B5. Analyze each TMW run

```bash
python scripts/04_analyze_tmw_bracketing.py --manifest data/manifest/my_tmw_manifest.csv
```

Check:

```text
outputs/04_tmw_run_analysis/run_plots/
outputs/04_tmw_run_analysis/tmw_run_metrics.csv
```

For each plot, verify:

- the high-speed initiation segment is visible;
- the selected constant `V_step` is correct;
- `L_weld`, `L_crack`, and `L*` are correct;
- failed/exploratory tests are marked `include_in_summary = no`.

## B6. Fit V_C--V_F for each condition

```bash
python scripts/05_fit_tmw_conditions.py
```

Outputs:

```text
outputs/05_tmw_condition_fits/tmw_condition_transition_summary.csv
outputs/05_tmw_condition_fits/condition_transition_plots/
```

Each condition plot shows `L*` versus `V_step` and the fitted `V_C`--`V_F` interval.

## B7. Compare all fitted conditions

```bash
python scripts/06_compare_tmw_conditions.py
```

Outputs:

```text
outputs/06_tmw_condition_comparison/Transition_ranges_summary.png
outputs/06_tmw_condition_comparison/tmw_condition_comparison_summary.csv
```

This is the final comparison across materials, filler wires, currents, preheats, or other process conditions.

---

# Part C: Reproduce manuscript processed-data figures only

Use this when you only want to regenerate the manuscript summary figures from the already processed CSV files:

```bash
python scripts/reproduce_all.py
```

This does not check the raw data or re-pick weld starts.

---

# Troubleshooting

## The calculated weld length looks shifted

Check:

```text
weld_start_time_s
manual_load_rise_time_s
manual_load_to_start_delay_s
weld_travel_speed_mm_s
```

## The temperature does not appear

Set in the manifest:

```text
show_temperature = yes
```

or set globally in:

```text
config/default_analysis_config.json
```

## The TMW condition fit fails

Usually this means the condition is not bracketed.  Add more TMW tests at lower or higher `V_step` values until no-crack and full-crack endpoints are included.

## A material name is not recognized

That is usually okay.  The code is material-agnostic.  Use any material name, but keep `condition_id` consistent across tests that belong together.
