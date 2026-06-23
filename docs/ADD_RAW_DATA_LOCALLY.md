# Add raw data locally after downloading the small package

This repository package does **not** include the raw controller logs.  This keeps
the download small.  Use this file to add the raw data you already have.

## Expected final folder structure

After adding the data, the repository should look like this:

```text
tmw_tmca_publication_repo_v9_code_only_add_raw_later/
  raw_data/
    TMCA/
      2025_12_29_TMCA/
      2025_12_30_TMCA/
      ...
    TMW/
      10_2025_TMW/
      2025_4_TMW/
      ...
  data/manifest/
    benny_tmca_manifest_prefilled.csv
    benny_tmw_manifest_prefilled.csv
```

The prefilled manifests already contain raw paths such as:

```text
raw_data/TMCA/2025_12_30_TMCA/B6F5SL_18.xml
raw_data/TMW/10_2025_TMW/B7F0SL5_7.xml
```

Therefore, do not change the manifest paths if you use the folder structure above.

## Option A: install from `raw_private.zip`

From the repository root, run:

```bash
python scripts/11_install_local_raw_data.py --zip "D:/path/to/raw_private.zip"
```

On PowerShell with your virtual environment:

```powershell
$PY = "d:\\טכניון\\תואר שלישי\\Reaserch Codes\\.venv\\Scripts\\python.exe"
& $PY scripts\\11_install_local_raw_data.py --zip "D:\\path\\to\\raw_private.zip"
```

The script accepts a zip whose internal folder is either:

```text
raw_private/TMCA/...
raw_private/TMW/...
```

or directly:

```text
TMCA/...
TMW/...
```

## Option B: install from an already extracted folder

If you already extracted the raw-data folder, run:

```bash
python scripts/11_install_local_raw_data.py --folder "D:/path/to/raw_private"
```

The folder can contain either `TMCA/` and `TMW/` directly, or it can contain a
nested `raw_private/TMCA` and `raw_private/TMW` structure.

## Manual copy option

You can also copy manually:

```powershell
New-Item -ItemType Directory -Force raw_data\\TMCA, raw_data\\TMW
Copy-Item -Recurse "D:\\path\\raw_private\\TMCA\\*" "raw_data\\TMCA\\"
Copy-Item -Recurse "D:\\path\\raw_private\\TMW\\*"  "raw_data\\TMW\\"
```

## Check that paths match the manifests

Run:

```bash
python scripts/check_environment.py
python scripts/10_run_benny_raw_data_workflow.py --limit-per-protocol 2
```

If the raw paths are correct, the quick test will convert two TMCA runs and two
TMW runs.  Then run the full workflow:

```bash
python scripts/10_run_benny_raw_data_workflow.py
```

Generated standardized CSV files and plots are written to:

```text
data/control_csv/tmca_raw/
data/control_csv/tmw_raw/
outputs/benny_raw_data/
```

These generated folders can be deleted and recreated at any time.
