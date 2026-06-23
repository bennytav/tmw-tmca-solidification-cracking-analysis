# TMW/TMCA solidification-cracking analysis workflow

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20812741.svg)](https://doi.org/10.5281/zenodo.20812741)

This repository contains the data, Python code, manifest files, and documentation required to reproduce the transverse-motion weldability (TMW) and transverse-motion crack-arrest (TMCA) analysis reported in the manuscript:

**An instrumented single-run transverse-motion crack-arrest test for rapid screening of solidification cracking in aluminum welds**

The repository supports two use cases:

1. Reproduce the processed results reported in the paper.
2. Analyze new TMCA and TMW tests from controller output files.

The workflow is material-agnostic. It can be used for AA6061, AA7075, AA5083, 304L stainless steel, Inconel alloys, magnesium alloys, or other weldable materials, provided that the required controller data, crack measurements, and experimental metadata are supplied in the manifest files.

---

## Repository contents

```text
.
├── README.md
├── START_HERE.md
├── ADD_LOCAL_RAW_DATA_AND_RUN.md
├── CITATION.cff
├── LICENSE
├── DATA_LICENSE_RECOMMENDATION.md
├── pyproject.toml
├── requirements.txt
├── config/
│   └── default_analysis_config.json
├── data/
│   ├── processed/
│   ├── manifest/
│   ├── control_csv_templates/
│   ├── examples/
│   └── raw/
├── raw_data/
│   ├── TMCA/
│   └── TMW/
├── docs/
├── scripts/
├── src/
│   └── tmw_tmca_analysis/
└── tests/
```

### Most important folders

- `src/tmw_tmca_analysis/`: reusable Python analysis functions.
- `scripts/`: command-line scripts for conversion, analysis, summaries, and plotting.
- `data/processed/`: processed CSV files used to reproduce the manuscript summary figures.
- `data/manifest/`: manifest files connecting each test to its metadata and crack measurements.
- `raw_data/TMCA/`: raw TMCA controller logs and metadata.
- `raw_data/TMW/`: raw TMW controller logs and metadata.
- `docs/`: detailed explanations for first-time users.
- `outputs/`: generated results. This folder is created when the scripts are run.

---

## Quick start

### 1. Clone the repository

```bash
git clone https://github.com/bennytav/tmw-tmca-solidification-cracking-analysis.git
cd tmw-tmca-solidification-cracking-analysis
```

### 2. Create a Python environment

Python 3.10 or newer is recommended.

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Check the environment

```bash
python scripts/check_environment.py
```

---

## Reproduce the manuscript summary results

To reproduce the processed manuscript summary figures and tables, run:

```bash
python scripts/reproduce_all.py
```

The outputs are written to:

```text
outputs/manuscript_reproduction/
```

This reproduction route uses the processed CSV files in `data/processed/`. It does not require re-converting the raw controller XML logs.

---

## Run the included raw-data workflow

If the raw controller logs are present in `raw_data/TMCA/` and `raw_data/TMW/`, first run a short test:

```bash
python scripts/10_run_benny_raw_data_workflow.py --limit-per-protocol 2
```

Then run the full workflow:

```bash
python scripts/10_run_benny_raw_data_workflow.py
```

The outputs are written to:

```text
outputs/benny_raw_data/
```

Inspect these folders:

```text
outputs/benny_raw_data/01_tmca_run_analysis/run_plots/
outputs/benny_raw_data/02_tmca_screening_summary/
outputs/benny_raw_data/04_tmw_run_analysis/run_plots/
outputs/benny_raw_data/05_tmw_condition_fits/
outputs/benny_raw_data/06_tmw_condition_comparison/
```

---

## Recommended analysis workflow for new tests

The code follows the experimental logic of the paper. Do not begin with the final summary plot. Begin by checking each individual run.

### Step 1 — Perform TMCA fast-screening tests

TMCA uses:

```text
V_high -> V_step -> constant deceleration a_dec
```

The goal is to estimate the crack-arrest velocity, `V_NC`, from one decelerating test. `V_NC` is used to select practical `V_step` values for later TMW testing. It should not be treated as identical to the constant-velocity TMW crack-free boundary `V_C`.

### Step 2 — Convert TMCA raw logs to standard CSV files

```bash
python scripts/07_convert_raw_xml_folder.py --input-dir raw_data/TMCA --output-dir data/control_csv/tmca_raw
```

### Step 3 — Create or edit the TMCA manifest

```bash
python scripts/08_create_manifest_scaffold.py --control-dir data/control_csv/tmca_raw --protocol TMCA --output-csv data/manifest/my_tmca_manifest.csv
```

Then open `data/manifest/my_tmca_manifest.csv` and fill the missing metadata and crack-position measurements.

### Step 4 — Select weld start manually, if needed

```bash
python scripts/09_pick_weld_start.py --manifest data/manifest/my_tmca_manifest.csv --run-id RUN_ID --write-manifest
```

In the interactive plot:

- zoom or pan using the Matplotlib toolbar;
- left-click to place or move the load-rise marker;
- right-click or press `c` to clear the marker;
- use the left/right arrow keys for fine adjustment;
- close the plot window only when the selected point is correct.

The selected value is saved only after the plot window is closed and confirmed.

### Step 5 — Analyze each TMCA run

```bash
python scripts/01_analyze_tmca_screening.py --manifest data/manifest/my_tmca_manifest.csv
```

Check every single-run plot before accepting the run:

```text
outputs/01_tmca_run_analysis/run_plots/
```

### Step 6 — Summarize TMCA screening results

```bash
python scripts/02_summarize_tmca_screening.py
```

Then generate an initial TMW test plan:

```bash
python scripts/03_plan_tmw_from_tmca.py
```

### Step 7 — Perform TMW bracketing tests

TMW uses:

```text
V_high -> constant V_step
```

For each material/process condition, perform several TMW tests using different `V_step` values. The goal is to bracket the transition from no crack propagation to full crack propagation.

### Step 8 — Convert TMW raw logs to standard CSV files

```bash
python scripts/07_convert_raw_xml_folder.py --input-dir raw_data/TMW --output-dir data/control_csv/tmw_raw
```

### Step 9 — Create or edit the TMW manifest

```bash
python scripts/08_create_manifest_scaffold.py --control-dir data/control_csv/tmw_raw --protocol TMW --output-csv data/manifest/my_tmw_manifest.csv
```

Then open `data/manifest/my_tmw_manifest.csv` and fill the missing metadata and crack-length measurements.

### Step 10 — Analyze each TMW run

```bash
python scripts/04_analyze_tmw_bracketing.py --manifest data/manifest/my_tmw_manifest.csv
```

Check every single-run plot:

```text
outputs/04_tmw_run_analysis/run_plots/
```

### Step 11 — Fit `V_C`--`V_F` for each condition

```bash
python scripts/05_fit_tmw_conditions.py
```

Inspect the condition-level transition plots:

```text
outputs/05_tmw_condition_fits/condition_transition_plots/
```

### Step 12 — Compare all TMW conditions

```bash
python scripts/06_compare_tmw_conditions.py
```

The condition-comparison results are written to:

```text
outputs/06_tmw_condition_comparison/
```

---

## Required input data

For each weld, the control system should provide one time-series file. The preferred public format is CSV, but this repository also includes scripts for converting the raw XML controller logs used in the study.

Required control columns:

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

If `weld_length_mm` is not present, the code calculates it from the weld-start time and the welding travel speed given in the manifest.

The controller log alone is not sufficient for the complete cracking analysis. The user must also provide crack-position measurements and experimental metadata in a manifest file.

---

## Manifest files

The manifest is the central file that controls the analysis. Each row corresponds to one weld test.

The code groups results by `condition_id`, not by hard-coded alloy names. Therefore, the same workflow can be used for new materials and conditions.

Example condition IDs:

```text
AA7075_ER5356_180A
AA7075_7075TiC_180A
AA6061_Autogenous_160A
AA5083_ER5356_160A
304L_Autogenous_120A
Inconel718_Filler_90A
```

Important TMCA manifest fields:

```text
run_id
protocol
control_csv
condition_id
base_material
filler_material
current_a
preheat_c
v_high_mm_s
v_step_mm_s
a_dec_mm_s2
weld_start_time_s
weld_travel_speed_mm_s
l_surf_mm
l_ct_mm
v_nc_mm_s
load_increase_acceptance
include_in_summary
```

Important TMW manifest fields:

```text
run_id
protocol
control_csv
condition_id
base_material
filler_material
current_a
preheat_c
v_high_mm_s
v_step_mm_s
weld_start_time_s
weld_travel_speed_mm_s
l_weld_mm
l_crack_mm
l_star
crack_state
include_in_summary
```

---

## Raw-data folder structure

Use this structure:

```text
raw_data/TMCA/<TMCA campaign folder>/...
raw_data/TMW/<TMW campaign folder>/...
```

Do not use these incorrect structures:

```text
raw_data/raw_private/TMCA/...
raw_data/raw_data/TMCA/...
raw_data/TMCA/TMCA/...
raw_data/TMW/TMW/...
```

Recommended raw-data contents:

```text
controller XML time-series logs
Parameters_*.xml controller metadata
*_metrics.json files
start_weld_overrides.json
mapping.xlsx
ID_dictionary.xlsx
TMW_summary.xlsx
original specimen/crack images, if needed for traceability
```

Generated plots, old duplicate scripts, temporary files, and working PDFs are not required for analysis.

---

## User-adjustable settings

Global options are stored in:

```text
config/default_analysis_config.json
```

Common settings include:

```text
show_temperature
selected_temperature_columns
weld_start_method
force_smoothing_window
plot_format
```

Individual runs can also override some settings in the manifest.

---

## Where to modify the code

The main analysis code is in:

```text
src/tmw_tmca_analysis/
```

Common modification points:

```text
Single-run plots:
src/tmw_tmca_analysis/plots.py
plot_single_run_control()

Manual weld-start picker:
scripts/09_pick_weld_start.py

Weld-start logic:
src/tmw_tmca_analysis/weld_start.py

Run-level metric extraction:
src/tmw_tmca_analysis/run_analysis.py
analyze_one_run()

TMCA V_NC summary:
src/tmw_tmca_analysis/metrics.py
summarize_tmca_vnc()

TMW V_C--V_F fitting:
src/tmw_tmca_analysis/metrics.py
fit_tmw_transition()

Summary figure style:
src/tmw_tmca_analysis/plots.py

Input-column definitions:
src/tmw_tmca_analysis/schema.py

Raw XML conversion:
src/tmw_tmca_analysis/raw_import.py
```

---

## Tests

Run the test suite with:

```bash
python -m pytest -q
```

---

## Citation

If you use this repository, please cite the archived Zenodo release:

B. Tavlovich, A. Shirizly, and S. Osovski, *Data and code for instrumented TMW/TMCA solidification-cracking analysis*, Zenodo, 2026. https://doi.org/10.5281/zenodo.20812741

A machine-readable citation file is included:

```text
CITATION.cff
```

---

## License

The code is distributed under the license stated in `LICENSE`.

For data licensing, see:

```text
DATA_LICENSE_RECOMMENDATION.md
```

Confirm the final code and data licenses with all authors and the institution before public release.

---

## Contact

For questions about the workflow, contact the corresponding author:

```text
Benny Tavlovich
bennytav@gmail.com
```
