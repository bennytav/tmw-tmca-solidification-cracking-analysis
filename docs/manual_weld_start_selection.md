# Manual weld-start selection from the load-rise signal

Use this guide when the automatic weld-start detection is not reliable.

## Why manual selection is used

The code calculates weld length from time when the controller CSV does not already contain `weld_length_mm`:

```text
weld_length_mm = (time_s - weld_start_time_s) * weld_travel_speed_mm_s
```

An error in `weld_start_time_s` shifts all crack-position mapping.  For this reason, the load-rise point should be checked for each new campaign.

## Command

For one TMCA run:

```bash
python scripts/09_pick_weld_start.py --manifest data/manifest/my_tmca_manifest.csv --run-id RUN_ID --write-manifest
```

For one TMW run:

```bash
python scripts/09_pick_weld_start.py --manifest data/manifest/my_tmw_manifest.csv --run-id RUN_ID --write-manifest
```

Without `--write-manifest`, the script writes a new file named `<manifest>_manual_start.csv`.

## How the plot works

The plot shows force and absolute transverse velocity versus time.

Controls:

```text
left-click        set or move the selected load-rise line
right-click       clear the selected point
c                 clear the selected point
left/right arrows fine adjustment after selecting a point
r                 reset the zoom
Matplotlib toolbar zoom/pan the graph
Enter             close the plot and accept the current marker
window close      close the plot and accept the current marker
Esc or q          clear and close
```

The selected point is not saved after the first click.  You can zoom, move the marker, and adjust it repeatedly.  The value is written to the manifest only after the figure is closed and confirmed in the terminal.

## What is written to the manifest?

The script writes:

```text
weld_start_method = manual_load_rise
manual_load_rise_time_s = selected time
manual_load_to_start_delay_s = selected delay
weld_start_time_s = selected time + selected delay
```

The default delay is in:

```text
config/default_analysis_config.json
```

or can be changed from the command line:

```bash
python scripts/09_pick_weld_start.py --manifest data/manifest/my_tmca_manifest.csv --run-id RUN_ID --delay-s 3.0 --write-manifest
```

## Non-interactive mode

If you already know the load-rise time:

```bash
python scripts/09_pick_weld_start.py --manifest data/manifest/my_tmca_manifest.csv --run-id RUN_ID --load-rise-time-s 12.345 --write-manifest
```

## Recommended practice

1. Select weld start manually for a few representative runs.
2. Compare the manual value with the automatic load-rise guide.
3. Use automatic detection only when it gives consistent results.
4. Always inspect the single-run plot after analysis.
