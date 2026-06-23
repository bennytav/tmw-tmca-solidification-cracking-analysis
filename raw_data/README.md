# Raw data folder

This package was delivered without the large raw-data files.

Place the raw folders here:

```text
raw_data/TMCA/<TMCA campaign folders and files>
raw_data/TMW/<TMW campaign folders and files>
```

For Benny Tavlovich's manuscript dataset, use one of these methods:

1. Run:

```bash
python scripts/11_install_local_raw_data.py --zip path/to/raw_private.zip --overwrite
```

2. Or manually copy:

```text
raw_private/TMCA/* -> raw_data/TMCA/
raw_private/TMW/*  -> raw_data/TMW/
```

The prefilled manuscript manifests already point to paths under `raw_data/TMCA` and `raw_data/TMW`.
