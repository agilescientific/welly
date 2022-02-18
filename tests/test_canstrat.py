"""
Define a suite of tests for the canstrat functions.
"""
from striplog import Striplog, Lexicon


def test_canstrat(well):
    """
    Test conversion of well to canstrat.
    """
    s = Striplog.from_csv('tests/assets/K90_strip_pred.csv', lexicon=Lexicon.default())
    well.data['test'] = s
    dat = well.to_canstrat(key='test',
                           log='K   90',
                           lith_field="component",
                           as_text=True
                           )

    s7 = "K   907   3960 3966L0                                                           "
    assert s7 in dat
