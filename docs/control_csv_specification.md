# Control CSV specification

Each weld must have one controller CSV file.  The workflow is material-agnostic;
the CSV describes the mechanical/thermal signal only, and the manifest describes
the material and welding condition.

## Required columns

```text
time_s
actuator_position_mm
actuator_velocity_mm_s
reaction_force_n
```

Units:

- `time_s`: seconds.
- `actuator_position_mm`: lower-sheet actuator position, mm.
- `actuator_velocity_mm_s`: lower-sheet transverse velocity, mm/s.
- `reaction_force_n`: load-cell reaction force, N.

## Optional columns

```text
weld_length_mm
temperature_1_c
temperature_2_c
temperature_3_c
temperature_4_c
```

If `weld_length_mm` is missing, the analysis calculates it as:

```text
weld_length_mm = (time_s - weld_start_time_s) * weld_travel_speed_mm_s
```

The weld-start time comes from the manifest or from load-rise detection.

## Accepted aliases

The loader also accepts common names from the original working scripts:

| Standard column | Accepted examples |
|---|---|
| `time_s` | `Time [s]`, `Time`, `t_s` |
| `actuator_position_mm` | `MotorPos`, `Motor position`, `Position [mm]` |
| `actuator_velocity_mm_s` | `Velocity [mm/s]`, `Velocity`, `transverse_velocity_mm_s` |
| `reaction_force_n` | `LoadCell`, `Load [N]`, `Force`, `Force_N` |
| `temperature_1_c` etc. | `Temper_1`, `Temp_1`, `Temperature_1` |

The aliases are renamed automatically when `load_control_csv()` is called.
