# -*- coding: utf 8 -*-
"""
Define a suite a tests for the Well module.
"""
import os
from pathlib import Path

from welly import Well


def test_well(well):
    # Check some basics.
    assert well.location.country == 'CA'
    assert len(well.data) == 24
    assert well.data['GR'][0] - 46.69865036 < 0.001
    assert len(well.survey_basis()) == 12718

    # This is garbled, but it is what it is.
    assert well.uwi == "Long = 63* 45'24.460  W"

    # Check we can retrieve item from header
    assert well.header[well.header.mnemonic == 'STRT'].value.iloc[0] == 1.0668

    # Check we can make one.
    assert well.to_lasio().well['FLD'].value == "Windsor Block"

    # Check we can add curves.
    well.add_curves_from_las(['tests/assets/1.las'])
    assert len(well.data['HCAL']) == 4  # New short curve.

    # Unify basis.
    # well.data['GR'] = well.data['GR'].to_basis(start=100, stop=200, step=1)
    assert len(well.data['HCAL']) != len(well.data['RHOB'])
    well.unify_basis()
    assert len(well.data['HCAL']) == len(well.data['RHOB'])


def test_well_pathlib():
    path = Path('tests/assets/P-129_out.LAS')
    well = Well.from_las(path)
    assert isinstance(well, Well)


def test_html_repr(well):
    html = well._repr_html_()

    name = """<table><tr><th style="text-align:center;" colspan="2">Kennetcook #2<br><small>Long = 63* 45'24.460  W</small></th></tr>"""
    data = """<tr><td><strong>data</strong></td><td>"""
    prov = """<tr><td><strong>province</strong></td><td>Nova Scotia</td></tr>"""
    assert name in html
    assert data in html
    assert prov in html
    for d in ['HCAL', 'RLA1', 'DT', 'DPHI_LIM', 'RLA3', 'RT_HRLT', 'CALI', 'DTS', 'DPHI_DOL', 'RLA5', 'RXO_HRLT',
              'RLA4', 'SP', 'RXOZ', 'NPHI_LIM', 'DPHI_SAN', 'RLA2', 'PEF', 'RHOB', 'NPHI_SAN', 'RM_HRLT', 'NPHI_DOL',
              'GR', 'DRHO']:
        assert d in html


def test_well_write(well):
    path = 'tests/assets/test.las'
    well.to_las(path)
    well = Well.from_las(path)
    assert well.data['GR'][0] - 46.69865036 < 0.001
    os.remove(path)
