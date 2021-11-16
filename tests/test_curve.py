# -*- coding: utf 8 -*-
"""
Define a suite a tests for the Curve module.
"""
import numpy as np
from pandas import RangeIndex

from welly.curve import Curve


def test_curve(curve):
    """
    Test basic stuff.
    """
    # Basics
    assert curve.shape[1] == 1
    assert curve.size == 12718
    assert curve.df.index.size == 12718

    # Check HTML repr.
    html = curve._repr_html_()
    base = """<table><tr><th style="text-align:center;" colspan="2">GR [gAPI]</th></tr><tr><td style="text-align:center;" colspan="2">1.0668 : 1939.1376 : 0.1524</td></tr><tr><td><strong>"""
    co = """<tr><td><strong>service_company</strong></td><td>Schlumberger</td></tr>"""
    null = """<tr><td><strong>null</strong></td><td>-999.25</td></tr>"""
    data = """<tr><th style="border-top: 2px solid #000;">Depth</th><th style="border-top: 2px solid #000;">Value</th></tr><tr><td>1.0668</td><td>46.6987</td></tr><tr><td>1.2192</td><td>46.6987</td></tr><tr><td>1.3716</td><td>46.6987</td></tr><tr><td>⋮</td><td>⋮</td></tr><tr><td>1938.8328</td><td>92.2462</td></tr><tr><td>1938.9852</td><td>92.2462</td></tr><tr><td>1939.1376</td><td>92.2462</td></tr></table>"""
    assert base in html
    assert co in html
    assert null in html
    assert data in html


def test_basis_numerical(curve):
    """
    Test basis change for numerical data.
    """
    curve_new = curve.to_basis(start=100, stop=200, step=1)
    assert curve_new.df.size == 101
    assert curve_new.df.iloc[0][0] - 66.6059 < 0.001

    curve_new2 = curve.to_basis_like(curve_new)
    assert curve_new2.df.size == 101
    assert curve_new2.df.iloc[0][0] - 66.6059 < 0.001


def test_basis_categorical():
    cat_data = ['sand'] * 20 + [np.nan] * 5 + ['cement'] * 10 + [np.nan] * 5
    curve_cat = Curve(cat_data, index=range(0, 40))
    curve_new = curve_cat.to_basis(start=5, stop=30, step=1)
    assert len(curve_new) == 26


def test_read_at(curve):
    """
    Test reading at index value for single number and array of numbers.
    """
    assert curve.read_at(1000) - 109.414177 < 0.001

    actual = curve.read_at([500, 1000, 1500])
    desired = np.array([91.29946709, 109.4141766, 64.55931458])
    np.testing.assert_allclose(actual, desired)


def test_assign_categorical(curve):
    assert curve.dtypes[0] == 'float'
    curve.dtypes = 'category'
    assert curve.dtypes[0] == 'category'


def test_block(curve):
    """
    Test log blocking.
    """
    b = curve.block(cutoffs=[50, 100])
    assert b.df.size == 12718
    assert b.index.size == 12718
    assert b.df.max()[0] == 2

    b = curve.block()
    assert b.df.mean()[0] - 0.46839 < 0.001

    b = curve.block(cutoffs=[50, 100, 110], values=[12, 24, 36, 40])
    assert b.df.max()[0] == 40
    assert b.df.mean()[0] - 26.072967 < 0.001


def test_despike(curve):
    """
    Test despiker with even window and z != 2.
    """
    assert curve.df.max()[0] - curve.despike(50, z=1).df.max()[0] - 91.83918 < 0.001


def test_repr_html_(curve):
    html = curve._repr_html_()
    assert html[77] == '<'


# define test data
data_num = np.linspace(1, 200, 20)
data_num_2d = np.array([data_num, np.linspace(400, 201, 20)]).T
data_cat = ['sand'] * 5 + ['channel'] * 5 + ['shale'] * 5 + ['cement'] * 5
data_cat_2d = np.array([data_cat, data_cat]).T
index = np.arange(20, 40)

# define curve attributes
mnemonic = 'GR'
mnemonic2d = ['GR[0]', 'GR[1]']
units = 'API'


def test_create_1d_curve():
    c = Curve(data=data_num)
    assert c.df.iloc[0, 0] == 1


def test_create_1d_curve_with_index_name():
    c = Curve(data=data_num, index_name='depth')
    assert c.df.index.name == 'depth'


def test_subset_1d_curve():
    c = Curve(data=data_num)
    c.df = c.df.iloc[5:15]
    assert c.df.iloc[0, 0] == 53.368421052631575


def test_create_1d_curve_no_mnemonic():
    c = Curve(data=data_num, index=index, units=units)
    assert c.df.index[1] == 21


def test_create_1d_curve_no_index():
    c = Curve(data=data_num, index=None, mnemonic=mnemonic, units=units)
    assert isinstance(c.df.index, RangeIndex)


def test_create_1d_curve_no_data():
    c = Curve(data=None, index=index, mnemonic=mnemonic, units=units)
    assert c.df.index[3] == 23


def test_create_1d_curve_no_data_and_index():
    c = Curve(data=None, index=None, mnemonic=mnemonic, units=units)
    assert c.df.empty
    assert c.units == 'API'


def test_create_1d_curve_categorical():
    c = Curve(data=data_cat, dtype='category')
    assert c.df.dtypes[0] == 'category'


def test_create_2d_curve_num():
    c = Curve(data=data_num_2d, mnemonic=mnemonic2d)
    assert c.df.shape == (20, 2)
    assert c.df.iloc[1, 1] == 389.5263157894737


def test_create_2d_curve_cat():
    c = Curve(data=data_cat_2d, mnemonic=mnemonic2d, dtype='category')
    assert c.df.shape == (20, 2)
    assert c.df.iloc[1, 1] == 'sand'


def test_curve_plot_2d():
    c = Curve(data=data_num, index=index, mnemonic=mnemonic)
    c.plot_2d()


def test_curve_plot():
    c = Curve(data=data_num, index=index, mnemonic=mnemonic)
    c.plot()


def test_curve_plot_kde():
    c = Curve(data=data_num, index=index, mnemonic=mnemonic)
    c.plot_kde()
