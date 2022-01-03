# -*- coding: utf 8 -*-
"""
Define a suite a tests for the canstrat functions.
"""
from welly import Well
import welly.quality as q

tests = {
    'Each': [
        q.no_flat,
        q.no_monotonic,
        q.no_gaps,
    ],
    'Gamma': [
        q.all_positive,
        q.all_below(450),
        q.check_units(['API', 'GAPI']),
    ],
    'DT': [
        q.all_positive,
    ],
    'Sonic': [
        q.all_between(1, 10000),  # 1333 to 5000 m/s
        q.no_spikes(10),          # 10 spikes allowed
    ],
}

alias = {
    "Gamma": ["GR", "GAM", "GRC", "SGR", "NGT"],
    "Density": ["RHOZ", "RHOB", "DEN", "RHOZ"],
    "Sonic": ["DT", "AC", "DTP", "DT4P"],
    "Caliper": ["CAL", "CALI", "CALS", "C1"],
    'Porosity SS': ['NPSS', 'DPSS'],
}


def test_quality():
    """
    Test basic stuff.
    """
    w = Well.from_las('tests/assets/P-129_out.LAS')
    r = w.qc_data(tests, alias=alias)
    assert len(r['GR'].values()) == 6
    assert sum(r['GR'].values()) == 3
    assert len(r['DT'].values()) == 6

    html = w.qc_table_html(tests, alias=alias)
    assert len(html) == 10057
    assert '<table><tr><th>Curve</th><th>Passed</th><th>Score</th>' in html
    assert '<tr><th>GR</th><td>3 / 6</td><td>0.500</td><td style=' in html

    r_curve_group = w.qc_curve_group(tests, alias=alias)
    assert isinstance(r_curve_group, dict)


def test_quality_curve():
    """
    Test qc functions in class Curve
    """
    w = Well.from_las('tests/assets/P-129_out.LAS')
    c = w.get_curve(mnemonic='CALI')

    tests_curve = c.quality(tests=tests)
    assert isinstance(tests_curve, dict)
    assert len(tests_curve) == 3

    tests_curve_qflag = c.qflag(tests=tests, alias=alias)
    assert isinstance(tests_curve_qflag, dict)
    assert len(tests_curve_qflag) == 3

    tests_curve_qflags = c.qflags(tests=tests, alias=alias)
    assert isinstance(tests_curve_qflags, dict)
    assert len(tests_curve_qflags) == 3

    test_score = c.quality_score(tests=tests_curve)
    assert test_score == -1
