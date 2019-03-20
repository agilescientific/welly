# -*- coding: utf 8 -*-
"""
Define a suite a tests for the Curve module.
"""
import numpy as np

from welly import Well
from welly import Curve

FNAME = 'tests/P-129_out.LAS'


def test_curve():
    """
    Test basic stuff.
    """
    well = Well.from_las(FNAME)
    gr = well.data['GR']

    # Basics
    assert gr.ndim == 1
    assert gr.size == 12718
    assert gr.basis.size == 12718

    # Check HTML repr.
    html = gr._repr_html_()
    base = """<table><tr><th style="text-align:center;" colspan="2">GR [gAPI]</th></tr><tr><td style="text-align:center;" colspan="2">1.0668 : 1939.1376 : 0.1524</td></tr><tr><td><strong>"""
    co = """<tr><td><strong>service_company</strong></td><td>Schlumberger</td></tr>"""
    null = """<tr><td><strong>null</strong></td><td>-999.25</td></tr>"""
    data = """<tr><th style="border-top: 2px solid #000;">Depth</th><th style="border-top: 2px solid #000;">Value</th></tr><tr><td>1.0668</td><td>46.6987</td></tr><tr><td>1.2192</td><td>46.6987</td></tr><tr><td>1.3716</td><td>46.6987</td></tr><tr><td>⋮</td><td>⋮</td></tr><tr><td>1938.8328</td><td>92.2462</td></tr><tr><td>1938.9852</td><td>92.2462</td></tr><tr><td>1939.1376</td><td>92.2462</td></tr></table>"""
    assert base in html
    assert co in html
    assert null in html
    assert data in html


def test_basis():
    """
    Test basis change.
    """
    well = Well.from_las(FNAME)
    gr = well.data['GR']

    x = gr.to_basis(start=100, stop=200, step=1)
    assert x.size == 101
    assert x[0] - 66.6059 < 0.001

    y = gr.to_basis_like(x)
    assert y.size == 101
    assert y[0] - 66.6059 < 0.001


def test_read():
    """
    Test reading for single number and array.
    """
    well = Well.from_las(FNAME)
    gr = well.data['GR']

    assert gr.read_at(1000) - 109.414177 < 0.001

    actual = gr.read_at([500, 1000, 1500])
    desired = np.array([91.29946709, 109.4141766, 64.55931458])
    np.testing.assert_allclose(actual, desired)


def test_block():
    """
    Test log blocking.
    """
    well = Well.from_las(FNAME)
    gr = well.data['GR']

    b = gr.block(cutoffs=[50, 100])
    assert b.size == 12718
    assert b.basis.size == 12718
    assert b.max() == 2

    b = gr.block()
    assert b.mean() - 0.46839 < 0.001

    b = gr.block(cutoffs=[50, 100], values=[12, 24, 36])
    assert b.max() == 36
    assert b.mean() - 25.077528 < 0.001


def test_despike():
    """
    Test despiker with even window and z != 2.
    """
    well = Well.from_las(FNAME)
    gr = well.data['GR']
    assert gr.max() - gr.despike(50, z=1).max() - 91.83918 < 0.001
