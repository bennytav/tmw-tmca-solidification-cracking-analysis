# Run manifest specification

The manifest is the central control file for the analysis.  One row represents
one weld.  The code can analyze arbitrary materials and conditions; it does not
assume that the material is AA6061 or AA7075.

## Required columns

```text
run_id
protocol
control_csv
```

`protocol` must be:

```text
TMCA
```

or

```text
TMW
```

## Important recommended columns

```text
condition_id
base_material
filler_material
weld_process
current_a
preheat_c
spacer_mm
v_high_mm_s
v_step_mm_s
a_dec_mm_s2
weld_start_method
weld_start_time_s
manual_load_rise_time_s
manual_load_to_start_delay_s
weld_travel_speed_mm_s
speed_transition_weld_length_mm
deceleration_start_weld_length_mm
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

## Condition grouping

The `condition_id` groups tests together.  Examples:

```text
AA5083_ER5356_160A
304L_Autogenous_120A
Inconel718_ERNiCr_90A
AA7075_7075TiC_180A
```

For TMW, all rows with the same `condition_id` are fitted together to obtain
one transition interval, `V_C--V_F`.  For TMCA, all rows with the same
`condition_id` are summarized together.

## Weld-start methods

Use the `weld_start_method` column:

| Method | Meaning |
|---|---|
| `manifest` | Use `weld_start_time_s`. |
| `manual_load_rise` | Use `manual_load_rise_time_s + manual_load_to_start_delay_s`. |
| `load_rise` | Detect the first load increase automatically. |
| `fixed_time` | Use `fixed_start_time_s`. |
| `manifest_or_load_rise` | Use manifest time if present, otherwise manual/automatic load-rise. |

The manual load-rise option reproduces the working procedure in which the user
selects the load-increase point and applies a delay to obtain the weld-start
coordinate.  Use `scripts/09_pick_weld_start.py` for this step.  The plot allows
zooming, panning, repeated clicks to move the marker, right-click/`c` to clear,
and saves the selected point only after the plot is closed and confirmed.

## TMCA-specific fields

TMCA velocity history:

```text
V_high -> V_step -> constant deceleration a_dec
```

Fill:

```text
v_high_mm_s
v_step_mm_s
a_dec_mm_s2
speed_transition_weld_length_mm
deceleration_start_weld_length_mm
l_surf_mm or l_crack_mm
```

If `v_nc_mm_s` is blank, the code interpolates the measured velocity at the
selected crack-end coordinate.

## TMW-specific fields

TMW velocity history:

```text
V_high -> constant V_step
```

Fill:

```text
v_high_mm_s
v_step_mm_s
l_weld_mm
l_crack_mm
```

If `l_star` is blank, the code calculates:

```text
L* = l_crack_mm / l_weld_mm
```

## Include/exclude decisions

Use:

```text
include_in_summary = yes
```

for valid runs and:

```text
include_in_summary = no
```

for tests that should be plotted and archived but excluded from summary fitting.
