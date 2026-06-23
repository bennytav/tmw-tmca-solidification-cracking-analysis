# Smoke-test results for v7

The package was checked in a clean container environment.

Commands checked:

```bash
python scripts/check_environment.py
python scripts/reproduce_all.py
python scripts/01_analyze_tmca_screening.py
python scripts/02_summarize_tmca_screening.py
python scripts/03_plan_tmw_from_tmca.py
python scripts/04_analyze_tmw_bracketing.py
python scripts/05_fit_tmw_conditions.py
python scripts/06_compare_tmw_conditions.py
python -m pytest -q
```

Results:

```text
Environment check passed.
Manuscript processed-data reproduction completed.
TMCA single-run analysis completed on example rows.
TMCA summary completed on example rows.
TMW single-run analysis completed on example rows.
TMW condition fitting completed on example rows.
TMW condition comparison completed on example rows.
3 tests passed.
```

The interactive weld-start picker cannot be fully tested in a headless container because it requires a local graphical window.  Its non-interactive mode was tested using:

```bash
python scripts/09_pick_weld_start.py --manifest data/manifest/_tmp_tmca_m.csv --run-id EXAMPLE_TMCA_001 --load-rise-time-s 12.345 --write-manifest --no-confirm
```

The command wrote:

```text
weld_start_method = manual_load_rise
manual_load_rise_time_s = 12.345
weld_start_time_s = 15.345
```
