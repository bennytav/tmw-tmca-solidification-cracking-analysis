# Configuration file

The main configuration file is:

```text
config/default_analysis_config.json
```

Most users do not need to edit Python code.  Change options here or in the manifest.

Important settings:

```json
"crack_end_preference": ["l_surf_mm", "l_crack_mm", "l_ct_mm"]
```
Controls which crack-end coordinate is used for TMCA `V_NC` if more than one is available.

```json
"show_temperature": false
```
Controls whether temperature curves are drawn in single-run plots.  This can also be overridden per run in the manifest.

```json
"manual_load_to_start_delay_s": 3.0
```
Delay added after the manually selected load-rise time to define the weld-start time.

```json
"material_colors"
```
Add material colors here if you want consistent colors for new materials such as AA5083, 304L, Inconel718, etc.
