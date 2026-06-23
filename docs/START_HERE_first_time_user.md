# Start here: first-time user workflow

## To run Benny Tavlovich's raw data first

This small download includes the code, processed data, and prefilled manifests,
but it does **not** include the large raw controller XML folder. Add your local
raw data first, then run the workflow.

If you have `raw_private.zip`:

```bash
python scripts/11_install_local_raw_data.py --zip path/to/raw_private.zip --overwrite
```

Then run:

```bash
python scripts/check_environment.py
python scripts/10_run_benny_raw_data_workflow.py --limit-per-protocol 2
python scripts/10_run_benny_raw_data_workflow.py
```

Detailed instructions are in:

```text
docs/ADD_RAW_DATA_LOCALLY.md
docs/RUN_INCLUDED_RAW_DATA.md
```

After you understand Benny's example, use the workflow below for your own new
TMCA/TMW tests.

---

This repository analyzes transverse-motion weldability (TMW) and transverse-motion crack-arrest (TMCA) tests.  It is designed so a new user can analyze new experiments, not only reproduce the published manuscript figures.

The workflow has two levels:

1. **Run-level analysis:** analyze each weld separately and check the plot.
2. **Campaign-level summary:** summarize only the runs that were checked and accepted.

Do not begin from the final summary.  Begin from the single-run plots.

---

## 1. What data must the control system export?

For each weld, export one CSV file with at least these columns:

```text
time_s
actuator_position_mm
actuator_velocity_mm_s
reaction_force_n
```

Recommended optional columns:

```text
temperature_1_c
temperature_2_c
temperature_3_c
temperature_4_c
weld_length_mm
```

If `weld_length_mm` is not included, the code calculates it from:

```text
weld_length_mm = (time_s - weld_start_time_s) * weld_travel_speed_mm_s
```

This is why weld-start selection is important.

---

## 2. What is the manifest?

The manifest is a CSV table with one row per weld.  It connects the controller CSV to the experimental metadata and crack measurements.

Minimum columns:

```text
run_id
protocol
control_csv
```

Important columns that the user normally fills:

```text
condition_id
base_material
filler_material
current_a
preheat_c
v_high_mm_s
v_step_mm_s
a_dec_mm_s2
weld_start_method
weld_start_time_s
manual_load_rise_time_s
manual_load_to_start_delay_s
weld_travel_speed_mm_s
l_weld_mm
l_crack_mm
l_surf_mm
l_ct_mm
l_star
v_nc_mm_s
include_in_summary
show_temperature
temperature_columns
```

Detailed column definitions are in:

```text
docs/run_manifest_specification.md
```

---

## 3. TMCA first: fast screening

TMCA velocity history:

```text
V_high -> V_step -> constant deceleration a_dec
```

Purpose: obtain screening values of `V_NC` and locate useful velocity ranges for later TMW bracketing.

### Step 3.1: create/fill the TMCA manifest

Use this template:

```text
data/manifest/blank_tmca_screening_manifest_template.csv
```

Save your working copy as:

```text
data/manifest/my_tmca_manifest.csv
```

### Step 3.2: manually select weld start, if needed

Use this when automatic weld-start detection is not correct.

```bash
python scripts/09_pick_weld_start.py --manifest data/manifest/my_tmca_manifest.csv --run-id RUN_ID --write-manifest
```

The plot is interactive:

- use the toolbar to zoom or pan;
- left-click to set or move the load-rise line;
- right-click or press `c` to clear;
- press the left/right arrow keys for fine adjustment;
- close the window or press Enter when finished;
- the value is written only after the plot is closed and confirmed.

### Step 3.3: analyze individual TMCA runs

```bash
python scripts/01_analyze_tmca_screening.py --manifest data/manifest/my_tmca_manifest.csv
```

Check every plot in:

```text
outputs/01_tmca_run_analysis/run_plots/
```

If a plot is wrong, fix the manifest row and rerun the script.

### Step 3.4: summarize TMCA

```bash
python scripts/02_summarize_tmca_screening.py
```

Outputs:

```text
outputs/02_tmca_screening_summary/tmca_screening_summary.csv
outputs/02_tmca_screening_summary/TMCA_transition_range_TMWstyle_box.png
outputs/02_tmca_screening_summary/recommended_tmw_vstep_plan.csv
```

`V_NC` is a screening metric.  It is not the same quantity as the constant-velocity TMW `V_C`.

---

## 4. Use TMCA to plan TMW

Create an initial plan for TMW `V_step` values:

```bash
python scripts/03_plan_tmw_from_tmca.py
```

The plan is only a starting point.  Add lower and higher `V_step` tests until each condition has no-crack and full-crack endpoints.

---

## 5. TMW bracketing

TMW velocity history:

```text
V_high -> constant V_step
```

For each condition, perform multiple TMW runs at different `V_step` values.

### Step 5.1: create/fill the TMW manifest

Use this template:

```text
data/manifest/blank_tmw_bracketing_manifest_template.csv
```

Save your working copy as:

```text
data/manifest/my_tmw_manifest.csv
```

All tests belonging to the same condition must have the same `condition_id`, for example:

```text
AA7075_ER5356_180A
AA5083_ER5356_160A
304L_Autogenous_120A
Inconel718_ERNiCr_90A
```

### Step 5.2: manually select weld start, if needed

```bash
python scripts/09_pick_weld_start.py --manifest data/manifest/my_tmw_manifest.csv --run-id RUN_ID --write-manifest
```

### Step 5.3: analyze individual TMW runs

```bash
python scripts/04_analyze_tmw_bracketing.py --manifest data/manifest/my_tmw_manifest.csv
```

Check every plot in:

```text
outputs/04_tmw_run_analysis/run_plots/
```

### Step 5.4: fit `V_C--V_F` for each condition

```bash
python scripts/05_fit_tmw_conditions.py
```

Outputs:

```text
outputs/05_tmw_condition_fits/tmw_condition_transition_summary.csv
outputs/05_tmw_condition_fits/condition_transition_plots/
```

If a condition is not bracketed, the code writes a warning.  That means more TMW tests are needed at lower or higher `V_step`.

---

## 6. Compare several TMW conditions

After fitting several conditions, create the comparison plot:

```bash
python scripts/06_compare_tmw_conditions.py
```

Output:

```text
outputs/06_tmw_condition_comparison/Transition_ranges_summary.png
```

---

## 7. Reproduce manuscript processed-data figures

This shortcut reproduces the published summary figures from the processed CSV tables:

```bash
python scripts/reproduce_all.py
```

Use this only to check the manuscript results.  For new experiments, use the full TMCA/TMW workflow above.

---

## 8. Where to change the code

| Goal | File/function |
|---|---|
| Change single-run plot style | `src/tmw_tmca_analysis/plots.py`, `plot_single_run_control()` |
| Show/hide temperature | Manifest columns `show_temperature`, `temperature_columns`, or `config/default_analysis_config.json` |
| Change weld-start logic | `src/tmw_tmca_analysis/run_analysis.py`, `determine_weld_start_time()` |
| Change TMCA `V_NC` extraction | `src/tmw_tmca_analysis/run_analysis.py`, `analyze_one_run()` |
| Change TMW `V_C--V_F` fitting | `src/tmw_tmca_analysis/metrics.py`, `fit_tmw_transition()` |
| Change final summary figures | `src/tmw_tmca_analysis/plots.py` |
| Change required input columns | `src/tmw_tmca_analysis/schema.py` |

---

## 9. Most common problems

### The module cannot be imported

Run scripts from the repository root, or use the packaged scripts, which automatically add `src/` to the Python path.

### The weld-length axis looks shifted

Check `weld_start_time_s`, `manual_load_rise_time_s`, `manual_load_to_start_delay_s`, and `weld_travel_speed_mm_s`.

### `V_NC` is blank

For TMCA, provide `l_surf_mm`, `l_crack_mm`, or `l_ct_mm`, and make sure the crack end lies inside the recorded weld-length range.

### TMW condition fitting gives a warning

The condition is not bracketed.  Perform additional TMW tests at lower or higher `V_step` values.
