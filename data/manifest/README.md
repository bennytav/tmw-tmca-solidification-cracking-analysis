# Manifest templates

A manifest is a CSV table with **one row per weld**.  It connects the controller CSV to the material/process condition, weld-start setting, and crack measurements.

Recommended workflow:

1. Copy the blank template.
2. Rename it to your working manifest, for example `my_tmca_manifest.csv`.
3. Fill one row per test.
4. Run `scripts/09_pick_weld_start.py` if weld start must be selected from the force trace.
5. Run the TMCA/TMW analysis script.
6. Check every single-run plot before making the summary.

Templates:

```text
blank_tmca_screening_manifest_template.csv   TMCA screening tests
blank_tmw_bracketing_manifest_template.csv   constant-velocity TMW tests
blank_run_manifest_template.csv              combined TMCA/TMW template
```

Important columns:

```text
run_id                   unique run name
protocol                 TMCA or TMW
control_csv              path to one standardized control CSV
condition_id             grouping variable for summaries
base_material            any material name, e.g., AA5083, AA7075, 304L, Inconel718
filler_material          Autogenous, ER5356, 7075TiC, or any user-defined filler
v_high_mm_s              initial high transverse velocity
v_step_mm_s              selected step velocity
a_dec_mm_s2              TMCA deceleration, positive value
weld_start_method        manifest, manual_load_rise, load_rise, fixed_time, manifest_or_load_rise
l_weld_mm                weld length used for L*
l_crack_mm               surface crack length for TMW L*
l_surf_mm                surface-visible crack end for TMCA V_NC
l_ct_mm                  CT internal crack end, if used
include_in_summary       yes/no
show_temperature         yes/no/auto
```

Full explanations are in:

```text
docs/run_manifest_specification.md
docs/START_HERE_first_time_user.md
```
