# Material and condition flexibility

The code is not limited to the manuscript materials.  It can analyze any TMW or
TMCA campaign if the manifest groups tests correctly.

## Examples

```text
base_material,filler_material,current_a,condition_id
AA5083,ER5356,160,AA5083_ER5356_160A
304L,Autogenous,120,304L_Autogenous_120A
Inconel718,ERNiCr,90,Inconel718_ERNiCr_90A
AA7075,7075TiC,180,AA7075_7075TiC_180A
```

The `condition_id` column is the grouping key.  For TMW, all rows with the same
condition_id are used together to fit one transition interval.  For TMCA, all
rows with the same condition_id are summarized together.

## Adding colors

For a new material, the code will automatically assign a deterministic color.
For a fixed color, edit:

```text
config/default_analysis_config.json
```

and add:

```json
"AA5083": "#4DAF4A",
"304L": "#984EA3",
"Inconel718": "#A65628"
```

inside `styles.material_colors`.
