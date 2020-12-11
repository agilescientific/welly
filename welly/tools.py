"""
Some extra bits.

:copyright: 2021 Agile Scientific
:license: Apache 2.0
"""
import numpy as np

from . import utils
from .curve import Curve


class RGBLog(object):
    """
    Attempt at RGB. Incomplete.
    """
    def __init__(self, curves):
        pass


def compute_position_log(deviation,
                         td=None,
                         method='mc',
                         azimuth_datum=0
                        ):
    """
    Args:
        deviation (ndarray): A deviation survey with rows like MD, INC, AZI
        td (Number): The TD of the well, if not the end of the deviation
            survey you're passing.
        method (str):
            'aa': average angle
            'bt': balanced tangential
            'mc': minimum curvature
        update_deviation: This function makes some adjustments to the dev-
            iation survey, to account for the surface and TD. If you do not
            want to change the stored deviation survey, set to False.
        azimuth_datum (Number): The orientation of the azimuth datum,
            relative to the y-axis.

    Returns:
        ndarray. A position log with rows like X-offset, Y-offset, Z-offset
    """
    deviation = np.array(deviation)

    # Adjust to TD.
    if td is not None:
        last_row = np.copy(deviation[-1, :])
        last_row[0] = td
        deviation = np.vstack([deviation, last_row])

    # Adjust to surface if necessary.
    if deviation[0, 0] > 0:
        deviation = np.vstack([np.array([0, 0, 0]), deviation])

    last = deviation[:-1] + [0, 0, azimuth_datum]
    this = deviation[1:] + [0, 0, azimuth_datum]

    diff = this[:, 0] - last[:, 0]

    Ia, Aa = np.radians(last[:, 1]), np.radians(last[:, 2])
    Ib, Ab = np.radians(this[:, 1]), np.radians(this[:, 2])

    if method == 'aa':
        Iavg = (Ia + Ib) / 2
        Aavg = (Aa + Ab) / 2
        delta_E = diff * np.sin(Iavg) * np.cos(Aavg)
        delta_N = diff * np.sin(Iavg) * np.sin(Aavg)
        delta_V = diff * np.cos(Iavg)
    elif method in ('bt', 'mc'):
        delta_E = 0.5 * diff * np.sin(Ia) * np.cos(Aa)
        delta_E += 0.5 * diff * np.sin(Ib) * np.cos(Ab)
        delta_N = 0.5 * diff * np.sin(Ia) * np.sin(Aa)
        delta_N += 0.5 * diff * np.sin(Ib) * np.sin(Ab)
        delta_V = 0.5 * diff * np.cos(Ia)
        delta_V += 0.5 * diff * np.cos(Ib)
    else:
        raise Exception("Method must be one of 'aa', 'bt', 'mc'")

    # Compute dogleg severity and ratio factor.
    _x = np.sin(Ib) * (1 - np.cos(Ab - Aa))
    dogleg = np.arccos(np.cos(Ib - Ia) - np.sin(Ia) * _x)
    dogleg[dogleg == 0] = 1e-12

    rf = 2 / dogleg * np.tan(dogleg / 2)
    rf[np.isnan(rf)] = 1

    if method == 'mc':
        delta_N *= rf
        delta_E *= rf
        delta_V *= rf

    # Prepare the output array.
    position = np.zeros_like(deviation, dtype=np.float)

    # Stack the results, add the surface.
    dogleg = np.hstack([[0], dogleg])
    _offsets = np.squeeze(np.dstack([delta_N, delta_E, delta_V]))
    _offsets = np.vstack([np.array([0, 0, 0]), _offsets])
    position += _offsets.cumsum(axis=0)

    return deviation, position, dogleg
