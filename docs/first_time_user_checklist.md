# First-time user checklist

Use this checklist before creating any summary plot.

## Before TMCA analysis

- [ ] One controller CSV exists for each TMCA weld.
- [ ] Each CSV contains `time_s`, `actuator_position_mm`, `actuator_velocity_mm_s`, and `reaction_force_n`.
- [ ] Temperature columns are present only if they were measured.
- [ ] The TMCA manifest has one row per weld.
- [ ] `condition_id` is filled consistently for tests that belong to the same condition.
- [ ] `base_material`, `filler_material`, and `current_a` are filled.
- [ ] `v_high_mm_s`, `v_step_mm_s`, and `a_dec_mm_s2` are filled.
- [ ] Crack-end coordinate is filled using `l_surf_mm`, `l_crack_mm`, or `l_ct_mm`.
- [ ] Weld start is known or selected using `scripts/09_pick_weld_start.py`.
- [ ] `show_temperature` is set to `yes`, `no`, or `auto`.
- [ ] `include_in_summary` is set to `yes` only for accepted runs.
- [ ] Single-run plots have been checked before running the TMCA summary.

## Before TMW analysis

- [ ] One controller CSV exists for each TMW weld.
- [ ] The TMW manifest has one row per weld.
- [ ] `condition_id` is the same for all tests in one condition.
- [ ] `v_high_mm_s` and `v_step_mm_s` are filled for every test.
- [ ] `l_weld_mm` and `l_crack_mm` are filled.
- [ ] `l_star` is filled or can be calculated as `l_crack_mm/l_weld_mm`.
- [ ] Weld start is known or selected using `scripts/09_pick_weld_start.py`.
- [ ] Each condition has enough different `V_step` values to bracket no crack and full crack.
- [ ] Failed/exploratory runs are marked `include_in_summary = no`.
- [ ] Single-run plots have been checked before fitting `V_C--V_F`.

## Before public upload

- [ ] Outputs were regenerated from a clean repository.
- [ ] The README and data dictionary match the released files.
- [ ] Private raw files remain in `raw_data/` and are not committed.
- [ ] License and data-sharing wording were approved by the authors/institution.
- [ ] GitHub release and Zenodo DOI were created, if using a public repository.
