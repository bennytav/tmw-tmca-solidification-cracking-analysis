# Add your local raw data and run the full workflow

This package intentionally does **not** include the large raw-data folder, so the download remains small. Use this package together with your local raw-data archive or local raw-data folders.

The expected final folder layout is:

```text
tmw_tmca_publication_repo_v9_code_only_add_raw_later/
├── raw_data/
│   ├── TMCA/
│   │   ├── 2025_12_29_TMCA/
│   │   ├── 2025_12_30_TMCA/
│   │   └── ...
│   └── TMW/
│       ├── 10_2025_TMW/
│       ├── 2026_3_6_TMW/
│       └── ...
├── data/
├── scripts/
└── src/
```

## Option A: you have `raw_private.zip`

Put your local `raw_private.zip` anywhere on your computer, then run:

```bash
python scripts/11_install_local_raw_data.py --zip path/to/raw_private.zip --overwrite
```

Example on Windows PowerShell:

```powershell
python scripts\11_install_local_raw_data.py --zip "D:\path\to\raw_private.zip" --overwrite
```

The script extracts:

```text
raw_private/TMCA/  -> raw_data/TMCA/
raw_private/TMW/   -> raw_data/TMW/
```

## Option B: you already extracted the raw folders

Copy the folders manually:

```text
raw_private/TMCA/*  ->  raw_data/TMCA/
raw_private/TMW/*   ->  raw_data/TMW/
```

Do not put the extra folder level inside `raw_data`. The correct path is:

```text
raw_data/TMCA/2025_12_29_TMCA/...
```

not:

```text
raw_data/raw_private/TMCA/2025_12_29_TMCA/...
```

## Run the manuscript raw-data workflow

After the raw data are in the correct place, run:

```bash
python scripts/check_environment.py
python scripts/10_run_benny_raw_data_workflow.py --limit-per-protocol 2
python scripts/10_run_benny_raw_data_workflow.py
```

The quick `--limit-per-protocol 2` command checks that conversion and analysis work before running all files.

Outputs are written to:

```text
outputs/benny_raw_data/
```

Important output folders:

```text
outputs/benny_raw_data/01_tmca_run_analysis/run_plots/
outputs/benny_raw_data/02_tmca_screening_summary/
outputs/benny_raw_data/04_tmw_run_analysis/run_plots/
outputs/benny_raw_data/05_tmw_condition_fits/
outputs/benny_raw_data/06_tmw_condition_comparison/
```

## Upload to GitHub

This small package can be pushed to GitHub first. After you add `raw_data/`, you can also commit the raw data if you decide to make it public.

Before pushing raw data, check file sizes:

```bash
python scripts/12_check_github_file_sizes.py
```

GitHub blocks regular Git files larger than 100 MiB and warns about files larger than 50 MiB. If the script reports a file above 100 MiB, do not push until that file is removed, split, or uploaded by another route such as Zenodo.
