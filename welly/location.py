#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines well location.

:copyright: 2016 Agile Geoscience
:license: Apache 2.0
"""
import numpy as np
from scipy.interpolate import interp1d

from . import utils
from .fields import las_fields
from .crs import CRS


class Location(object):
    def __init__(self, params):
        """
        Generic initializer for now.
        """
        self.td = None
        self.crs = CRS(params.pop('crs', dict()))

        for k, v in params.items():
            if k and v:
                setattr(self, k, v)

        if getattr(self, 'deviation', None) is None:
            self.deviation = None
            self.position = None
        else:
            td = self.td or getattr(self, 'TDD', getattr(self, 'TDL', None))
            self.compute_position_log(td=td)

    def __repr__(self):
        return 'Location({})'.format(self.__dict__)

    @classmethod
    def from_lasio(cls, l, remap=None, funcs=None):
        """
        Assumes we're starting with a lasio object, l.
        """
        params = {}
        for field, (sect, code) in las_fields['location'].items():
            params[field] = utils.lasio_get(l,
                                            sect,
                                            code,
                                            remap=remap,
                                            funcs=funcs)
        return cls(params)

    def add_deviation(self, dev, td=None):
        self.deviation = dev
        self.compute_position_log(td=td)
        return

    @property
    def md(self):
        return self.deviation[:, 0]  # First column of deviation survey.

    @property
    def tvd(self):
        return self.position[:, 2]  # Last column of position log.

    @property
    def md2tvd(self, kind='linear'):
        if self.position is None:
            return lambda x: x
        return interp1d(self.md, self.tvd,
                        kind=kind,
                        assume_sorted=True,
                        fill_value="extrapolate",
                        bounds_error=False)

    @property
    def tvd2md(self, kind='linear'):
        if self.position is None:
            return lambda x: x
        return interp1d(self.tvd, self.md,
                        kind=kind,
                        assume_sorted=True,
                        fill_value="extrapolate",
                        bounds_error=False)

    def compute_position_log(self,
                             td=None,
                             method='mc',
                             update_deviation=True):
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

        Returns:
            ndarray. A position log with rows like X-offset, Y-offset, Z-offset
        """
        deviation = np.copy(self.deviation)

        # Adjust to TD.
        if td is not None:
            last_row = np.copy(deviation[-1, :])
            last_row[0] = td
            deviation = np.vstack([deviation, last_row])

        # Adjust to surface if necessary.
        if deviation[0, 0] > 0:
            deviation = np.vstack([np.array([0, 0, 0]), deviation])

        last = deviation[:-1]
        this = deviation[1:]

        diff = this[:, 0] - last[:, 0]

        Ia, Aa = np.radians(last[:, 1]), np.radians(last[:, 2])
        Ib, Ab = np.radians(this[:, 1]), np.radians(this[:, 2])

        if method == 'aa':
            Iavg = (Ia + Ib) / 2
            Aavg = (Aa + Ab) / 2
            delta_N = diff * np.sin(Iavg) * np.cos(Aavg)
            delta_E = diff * np.sin(Iavg) * np.sin(Aavg)
            delta_V = diff * np.cos(Iavg)
        elif method in ('bt', 'mc'):
            delta_N = 0.5 * diff * np.sin(Ia) * np.cos(Aa)
            delta_N += 0.5 * diff * np.sin(Ib) * np.cos(Ab)
            delta_E = 0.5 * diff * np.sin(Ia) * np.sin(Aa)
            delta_E += 0.5 * diff * np.sin(Ib) * np.sin(Ab)
            delta_V = 0.5 * diff * np.cos(Ia)
            delta_V += 0.5 * diff * np.cos(Ib)
        else:
            raise Exception("Method must be one of 'aa', 'bt', 'mc'")

        if method == 'mc':
            _x = np.sin(Ib) * (1 - np.cos(Ab - Aa))
            dogleg = np.arccos(np.cos(Ib - Ia) - np.sin(Ia) * _x)
            dogleg[dogleg == 0] = 1e-9
            rf = 2 / dogleg * np.tan(dogleg / 2)  # ratio factor
            rf[np.isnan(rf)] = 1  # Adjust for NaN.
            delta_N *= rf
            delta_E *= rf
            delta_V *= rf

        # Prepare the output array.
        result = np.zeros_like(deviation, dtype=np.float)

        # Stack the results, add the surface.
        _offsets = np.squeeze(np.dstack([delta_N, delta_E, delta_V]))
        _offsets = np.vstack([np.array([0, 0, 0]), _offsets])
        result += _offsets.cumsum(axis=0)

        if update_deviation:
            self.deviation = deviation

        self.position = result

        return
