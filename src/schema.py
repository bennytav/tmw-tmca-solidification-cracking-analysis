"""Column definitions for the TMW/TMCA analysis workflow.

The workflow is intentionally material-agnostic.  It can be used for AA6061,
AA7075, AA5083, stainless steel 304L, Inconel, or any other alloy, provided the
manifest describes the condition and the controller CSV contains the required
signals.
"""

CONTROL_REQUIRED = {
    "time_s",
    "actuator_position_mm",
    "actuator_velocity_mm_s",
    "reaction_force_n",
}

CONTROL_OPTIONAL = {
    "temperature_1_c",
    "temperature_2_c",
    "temperature_3_c",
    "temperature_4_c",
    "weld_length_mm",
}

# Minimum columns needed to locate one control file and know which protocol it is.
# Other columns are recommended and are added as blank columns if missing.
MANIFEST_REQUIRED = {
    "run_id",
    "protocol",
    "control_csv",
}

MANIFEST_RECOMMENDED = [
    "run_id", "protocol", "control_csv", "test_date_iso", "condition_id",
    "material_category", "base_material", "filler_material", "weld_process",
    "current_a", "voltage_v", "heat_input_kj_mm", "shielding_gas", "preheat_c",
    "spacer_mm", "sheet_thickness_mm", "k_factor",
    "v_high_mm_s", "v_step_mm_s", "a_dec_mm_s2",
    "weld_start_method", "weld_start_time_s", "manual_load_rise_time_s",
    "manual_load_to_start_delay_s", "fixed_start_time_s", "load_rise_delta_n",
    "load_baseline_window_s", "weld_end_time_s", "weld_travel_speed_mm_s",
    "speed_transition_weld_length_mm", "deceleration_start_weld_length_mm",
    "l_weld_mm", "l_crack_mm", "l_surf_mm", "l_ct_mm", "l_star",
    "v_nc_mm_s", "crack_state", "load_increase_acceptance",
    "include_in_summary", "show_temperature", "temperature_columns", "notes",
]

RUN_METRIC_COLUMNS = [
    "run_id", "protocol", "test_date_iso", "condition_id", "material_category",
    "base_material", "filler_material", "weld_process", "current_a", "voltage_v",
    "heat_input_kj_mm", "shielding_gas", "preheat_c", "spacer_mm",
    "sheet_thickness_mm", "k_factor", "v_high_mm_s", "v_step_mm_s",
    "a_dec_mm_s2", "weld_start_method", "weld_start_source",
    "manual_load_rise_time_s", "manual_load_to_start_delay_s",
    "weld_start_time_s", "weld_end_time_s", "weld_travel_speed_mm_s",
    "speed_transition_weld_length_mm", "deceleration_start_weld_length_mm",
    "l_weld_mm", "l_crack_mm", "l_surf_mm", "l_ct_mm", "crack_end_source",
    "l_star", "v_nc_mm_s", "crack_state", "load_increase_acceptance",
    "include_in_summary", "max_force_n", "force_at_crack_end_n",
    "mean_preweld_temperature_c", "max_temperature_c", "show_temperature",
    "temperature_columns", "control_csv", "notes",
]

RUN_METRICS_COLUMNS = RUN_METRIC_COLUMNS
