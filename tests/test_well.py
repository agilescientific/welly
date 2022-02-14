# -*- coding: utf 8 -*-
"""
Define a suite a tests for the Well module.
"""
import os
from pathlib import Path

import welly
from welly import Well


def test_well(well):
    """
    Test loading wells with various meta data
    """
    # Check some basics.
    assert well.location.country == 'CA'
    assert len(well.data) == 24
    assert well.data['GR'].df.iloc[0][0] - 46.69865036 < 0.001
    assert len(well.survey_basis()) == 12718

    # This is garbled, but it is what it is.
    assert well.uwi == "Long = 63* 45'24.460  W"

    # Check we can retrieve item from header
    assert well.header[well.header.mnemonic == 'STRT'].value.iloc[0] == 1.0668

    # Check we can make one.
    assert well.to_lasio().well['FLD'].value == "Windsor Block"

    # Check we can add curves.
    well.add_curves_from_las(['tests/assets/1.las'])
    assert len(well.data['HCAL'].df) == 4  # New short curve.

    # Unify basis.
    # well.data['GR'] = well.data['GR'].to_basis(start=100, stop=200, step=1)
    assert len(well.data['HCAL'].df) != len(well.data['RHOB'].df)
    well.unify_basis()
    assert len(well.data['HCAL'].df) == len(well.data['RHOB'].df)


def test_set_uwi(well):
    well.uwi = 'test'
    assert well.uwi == 'test'


def test_well_remap_index():
    """
    Test loading a well and remapping the index name upon load time
    """
    path = Path('tests/assets/P-129_out.LAS')
    well = Well.from_las(path, remap={'DEPT': 'DEPTH'})
    assert well.data['GR'].index.name == 'DEPTH'


def test_well_pathlib():
    """
    Test loading a well from a `Path` instance
    """
    path = Path('tests/assets/P-129_out.LAS')
    well = Well.from_las(path)
    assert isinstance(well, Well)


def test_html_repr(well):
    """
    Test html representation of a well for Jupyter notebooks.
    """
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
    """
    Test writing a well to a .las file
    """
    path = 'tests/assets/test.las'
    well.to_las(path)
    well = Well.from_las(path)
    assert well.data['GR'].df.iloc[0][0] - 46.69865036 < 0.001
    os.remove(path)


def test_df(well):
    """
    Test creating a pd.DataFrame from a well
    """
    df = well.df()
    assert df.iloc[10, 2] - 3.586400032 < 0.001
    assert df.shape == (12718, 24)

    # test with keyword arguments
    alias = {'Gamma': ['GR', 'GRC', 'NGT'], 'Caliper': ['HCAL', 'CALI']}
    keys = ['Caliper', 'Gamma', 'DT']
    df = well.df(keys=keys, alias=alias, uwi=True)
    assert df.iloc[10, 1] - 46.69865036 < 0.001
    assert df.shape == (12718, 3)


def test_read_df(df):
    """
    Test creating a well from a pd.DataFrame with different arguments
    """
    well = Well.from_df(df)
    assert well.data['GR'].shape == (3, 1)
    well = Well.from_df(df, units={'GR': 'API', 'DEN': 'kg/m3'}, name='WELL1')
    assert well.data['GR'].units == 'API'
    assert well.name == 'WELL1'
    well = Well.from_df(df, req=['GR'], uwi='1001', name='WELL1')
    assert well.data['GR'].shape == (3, 1)
    assert well.uwi == '1001'

    well = welly.read_df(df)
    assert well.data['GR'].shape == (3, 1)


def test_assign_categorical(well):
    """
    Test assigning category dtype to multiple curves in a well.
    """
    well.assign_categorical(['RXOZ', 'RXO_HRLT'])
    assert well.data['RXOZ'].dtypes[0] == 'category'


def test_iter_well(well):
    """
    Test iterating over curves in a well
    """
    for curve in well:
        assert curve == well.data['CALI']
        break
