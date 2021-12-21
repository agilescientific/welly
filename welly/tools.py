"""
Some extra bits.

:copyright: 2021 Agile Scientific
:license: Apache 2.0
"""
import numpy as np
import wellpathpy as wp
import warnings


def compute_position_log(deviation,
                         td=None,
                         method='mc',
                         azimuth_datum=0,
                         course_length=1,
                         ):
    """Use wellpathpy to return the required welly objects

    Args:
        deviation (ndarray): A deviation survey with rows like MD, INC, AZI
        td (float): The TD of the well, if not the end of the deviation
            survey you're passing.
        method (str):
            'mc': minimum curvature
            'aa': average angle
            'bt': balanced tangential
            'hi': high tangential
            'lo': low tangential
            'rc': radius of curvature
        azimuth_datum (float): The orientation of the azimuth datum, relative
            to the y-axis.
        course_length (float): Default: 1. The length over which to normalize
            the dogleg severity. Typical values are 30 m or 100 ft. Use 1 for
            no normalization. Note: from v0.5, default will be 30.

    Returns:
        ndarray. A position log with rows like X-offset, Y-offset, Z-offset
    """
    deviation = np.asanyarray(deviation)

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

    # Make wellpathpy deviation object.
    dev = wp.deviation(*deviation.T)

    # Compute position log.
    methods = {
        'mc': dev.minimum_curvature(course_length),
        'rc': dev.radius_curvature(),
        'aa': dev.tan_method(),
        'bt': dev.tan_method(choice='bal'),
        'hi': dev.tan_method(choice='high'),
        'lo': dev.tan_method(choice='low'),
    }
    try:
        pos = methods[method]
    except KeyError:
        msg = 'Unknown choice of method: {}. '.format(method)
        msg += 'Method must be one of mc, aa, bt, hi, lo, or rc.'
        raise KeyError(msg)

    # Convert to welly formats.
    # deviation = np.hstack((dev.md, dev.inc, dev.azi))
    position = np.stack([pos.easting, pos.northing, pos.depth]).T
    dogleg = dev.minimum_curvature(course_length=course_length).dls

    return deviation, position, dogleg
