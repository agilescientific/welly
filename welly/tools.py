"""
Some extra bits.

:copyright: 2021 Agile Scientific
:license: Apache 2.0
"""
import numpy as np
import wellpathpy as wp

from . import utils
from .curve import Curve


class RGBLog(object):
    """
    Attempt at RGB. Incomplete.
    """
    def __init__(self, curves):
        pass


def compute_position_log(deviation, td=None, method='mc', azimuth_datum=0):
    """Use wellpathpy to return the required welly objects

    Args:
        deviation (ndarray): A deviation survey with rows like MD, INC, AZI
        td (Number): The TD of the well, if not the end of the deviation
            survey you're passing.
        method (str):
            'mc': minimum curvature
            'aa': average angle
            'bt': balanced tangential
            'hi': high tangential
            'lo': low tangential
            'rc': radius of curvature

        update_deviation: This function makes some adjustments to the dev-
            iation survey, to account for the surface and TD. If you do not
            want to change the stored deviation survey, set to False.
        azimuth_datum (Number): The orientation of the azimuth datum,
            relative to the y-axis.

    Returns:
        ndarray. A position log with rows like X-offset, Y-offset, Z-offset
    """

    # Adjust to TD.
    if td is not None:
        last_row = np.copy(deviation[-1, :])
        last_row[0] = td
        deviation = np.vstack([deviation, last_row])

    # Adjust to surface if necessary.
    if deviation[0, 0] > 0:
        deviation = np.vstack([np.array([0, 0, 0]), deviation])

    # Adjust to azimuth_datum.
    deviation += [0, 0, azimuth_datum]

    # Make wellpathpy objects
    md, inc, azi = np.split(deviation, 3, 1)
    dev = wp.deviation(md, inc, azi)

    if method == 'mc':
        pos = dev.minimum_curvature()
    elif method == 'aa':
        pos = dev.tan_method()
    elif method == 'bt':
        pos = dev.tan_method(choice='bal')
    elif method == 'hi':
        pos = dev.tan_method(choice='high')
    elif method == 'lo':
        pos = dev.tan_method(choice='low')
    elif method == 'rc':
        pos = dev.radius_curvature()
    else:
        msg = 'uknown choice {}, must be one of {}'
        methods = 'mc aa bt hi lo rc'.split()
        raise ValueError(msg.format(method, ' '.join(methods)))

    # Convert to welly formats
    deviation = np.hstack((dev.md, dev.inc, dev.azi))
    position = np.hstack((pos.easting.reshape(-1, 1), pos.northing.reshape(-1, 1), pos.depth.reshape(-1, 1)))
    dogleg = dev.minimum_curvature().dls.reshape(-1, 1)

    return deviation, position, dogleg
