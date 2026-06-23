# Run Benny Tavlovich's raw data

This smaller package does **not** include the large raw-data files. Add the raw data first, then run the workflow.

## 1. Add raw data

If you have `raw_private.zip`, run:

```bash
python scripts/11_install_local_raw_data.py --zip path/to/raw_private.zip --overwrite
```

If the raw data are already extracted, copy:

```text
raw_private/TMCA/* -> raw_data/TMCA/
raw_private/TMW/*  -> raw_data/TMW/
```

Correct final layout:

```text
raw_data/TMCA/2025_12_29_TMCA/...
raw_data/TMW/2026_3_6_TMW/...
```

## 2. Run quick test

```bash
python scripts/check_environment.py
python scripts/10_run_benny_raw_data_workflow.py --limit-per-protocol 2
```

## 3. Run full workflow

```bash
python scripts/10_run_benny_raw_data_workflow.py
```

Outputs are written to:

```text
outputs/benny_raw_data/
```

## 4. Check GitHub file sizes before upload

If you plan to push the raw data to GitHub, run:

```bash
python scripts/12_check_github_file_sizes.py
```

If any file is larger than 100 MiB, GitHub will block a normal Git push for that file.
