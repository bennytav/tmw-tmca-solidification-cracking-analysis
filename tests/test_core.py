from pathlib import Path
import numpy as np
import pandas as pd

from tmw_tmca_analysis.metrics import fit_tmw_transition, piecewise_transition, summarize_tmca_vnc


def test_piecewise_transition_bounds():
    y = piecewise_transition([0.05, 0.10, 0.15], 0.08, 0.12)
    assert np.allclose(y, [0.0, 0.5, 1.0])


def test_tmw_fit_bracketed_example():
    fit = fit_tmw_transition([0.06, 0.08, 0.095, 0.11, 0.13], [0.0, 0.10, 0.55, 1.0, 1.0])
    assert 0.05 < fit.v_c_mm_s < 0.09
    assert 0.10 <= fit.v_f_mm_s <= 0.13


def test_tmca_summary():
    df = pd.DataFrame({
        "condition_id": ["AA7075_ER5356_180A", "AA7075_ER5356_180A"],
        "base_material": ["7075", "7075"],
        "filler_material": ["ER5356", "ER5356"],
        "current_a": [180, 180],
        "spacer_mm": [3.6, 3.6],
        "v_nc_mm_s": [0.09, 0.11],
    })
    out = summarize_tmca_vnc(df)
    assert len(out) == 1
    assert abs(out.loc[0, "v_nc_mean_mm_s"] - 0.10) < 1e-12
