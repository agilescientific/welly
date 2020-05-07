# -*- coding: utf-8 -*-
"""
Defines well location.

:copyright: 2016 Agile Geoscience
:license: Apache 2.0
"""
import numpy as np
from scipy.interpolate import interp1d
from scipy.interpolate import splprep
from scipy.interpolate import splev
import warnings
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D 

from . import utils
from .fields import las_fields
from .crs import CRS


class Location(object):
    """
    Contains all location and spatial information.
    """
    def __init__(self, params=None):
        self.td = None
        self.crs = CRS(params.pop('crs', dict()))

        if params is None:
            params = {}

        for k, v in params.items():
            if k and (v is not None):
                try:
                    v_ = float(v.replace(',', ''))
                    if not np.isinf(v_):
                        setattr(self, k, v_)
                    else:
                        setattr(self, k, v)
                except:
                    setattr(self, k, v)

        if getattr(self, 'deviation', None) is None:
            self.deviation = None
            self.position = None
        else:
            td = self.td or getattr(self, 'TDD', getattr(self, 'TDL', None))
            self._compute_position_log(td=td)

    def __repr__(self):
        return 'Location({})'.format(self.__dict__)

    def crs_from_epsg(self, epsg):
        """
        Sets the CRS using an EPSG code.

        Args:
            epsg (int): The EPSG code.

        Returns:
            None.
        """
        self.crs = CRS.from_epsg(epsg)
        return

    def crs_from_string(self, string):
        """
        Sets the CRS using a PROJ4 string.

        Args:
            string (int): The PROJ4 string, eg '+init=epsg:4269 +no_defs'.

        Returns:
            None.
        """
        self.crs = CRS.from_string(string)
        return

    @classmethod
    def from_lasio(cls, l, remap=None, funcs=None):
        """
        Make a Location object from a lasio object. Assumes we're starting
        with a lasio object, l.

        Args:
            l (lasio).
            remap (dict): Optional. A dict of 'old': 'new' LAS field names.
            funcs (dict): Optional. A dict of 'las field': function() for
                implementing a transform before loading. Can be a lambda.

        Returns:
            Location. An instance of this class.
        """
        params = {}
        funcs = funcs or {}
        funcs['location'] = str
        for field, (sect, code) in las_fields['location'].items():
            params[field] = utils.lasio_get(l,
                                            sect,
                                            code,
                                            remap=remap,
                                            funcs=funcs)
        return cls(params)

    def add_deviation(self,
                      deviation,
                      td=None,
                      method='mc',
                      update_deviation=True,
                      azimuth_datum=0):
        """
        Add a deviation survey to this instance, and try to compute a position
        log from it.
        """
        try:
            dev_new, pos, dog = self._compute_position_log(deviation,
                                                        td,
                                                        method,
                                                        azimuth_datum,
                                                        )
        except:
            warnings.warn("The position log could not be computed.")
            dev_new, pos, dog = deviation, None, None

        if update_deviation:
            self.deviation = dev_new
        else:
            self.deviation = deviation
        self.position = pos
        self.dogleg = dog

        return

    @property
    def md(self):
        """
        The measured depth of the deviation survey.

        Returns:
            ndarray.
        """
        return self.deviation[:, 0]  # First column of deviation survey.

    @property
    def tvd(self):
        """
        The true vertical depth of the deviation survey.

        Returns:
            ndarray.
        """
        return self.position[:, 2]  # Last column of position log.

    @property
    def md2tvd(self, kind='linear'):
        """
        Provides an transformation and interpolation function that converts
        MD to TVD.

        Args:
            kind (str): The kind of interpolation to do, e.g. 'linear',
                'cubic', 'nearest'.

        Returns:
            function.
        """
        if self.position is None:
            return lambda x: x
        return interp1d(self.md, self.tvd,
                        kind=kind,
                        assume_sorted=True,
                        fill_value="extrapolate",
                        bounds_error=False)

    @property
    def tvd2md(self, kind='linear'):
        """
        Provides an transformation and interpolation function that converts
        MD to TVD.

        Args:
            kind (str): The kind of interpolation to do, e.g. 'linear',
                'cubic', 'nearest'.

        Returns:
            function.
        """
        if self.position is None:
            return lambda x: x
        return interp1d(self.tvd, self.md,
                        kind=kind,
                        assume_sorted=True,
                        fill_value="extrapolate",
                        bounds_error=False)

    def _compute_position_log(self,
                              deviation,
                              td=None,
                              method='mc',
                              azimuth_datum=0):
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
        dogleg[dogleg == 0] = 1e-9

        rf = 2 / dogleg * np.tan(dogleg / 2)
        rf[np.isnan(rf)] = 1

        if method == 'mc':
            delta_N *= rf
            delta_E *= rf
            delta_V *= rf

        # Prepare the output array.
        position = np.zeros_like(deviation, dtype=np.float)

        # Stack the results, add the surface.
        _offsets = np.squeeze(np.dstack([delta_N, delta_E, delta_V]))
        _offsets = np.vstack([np.array([0, 0, 0]), _offsets])
        position += _offsets.cumsum(axis=0)

        return deviation, position, dogleg

    def trajectory(self, datum=None, elev=True, points=1000, **kwargs):
        """
        Get regularly sampled well trajectory. Assumes there is a position
        log already, e.g. resulting from calling `add_deviation()` on a
        deviation survey.

        Args:
            datum (array-like): A 3-element array with adjustments to (x, y, z).
                For example, the x-position, y-position, and KB of the tophole
                location.
            elev (bool): In general the (x, y, z) array of positions will have
                z as TVD, which is positive down. If `elev` is True, positive
                will be upwards.
            points (int): The number of points in the trajectory.
            kwargs: Will be passed to `scipy.interpolate.splprep()`.

        Returns:
            ndarray. An array with shape (`points` x 3) representing the well
                trajectory. Columns are (x, y, z). 
        """
        pos = self.position.copy()

        if elev:
            # First check that 3rd column is actually depth, not elevation.
            if (pos[1, -1] - pos[0, -1]) > 0:
                pos *= [1, 1, -1]

        if datum is not None:
            pos += datum

        # Compute the spline and return as an array instead of as vectors.
        knees, _ = splprep(pos.T, k=3, **kwargs)
        spline = splev(np.linspace(0, 1, points), knees)
        return np.array(spline).T

    def plot_3d(self, ax=None, **kwargs):
        """
        Make a 3D plot of the well trajectory.
        """
        return_ax = True
        if ax is None:
            fig, ax = plt.subplots(figsize=(15, 7), subplot_kw={'projection': '3d'})
            return_ax = False

        ax.plot(*self.trajectory().T, lw=3, alpha=0.75)
        ax.set_xlabel('X position')
        ax.set_ylabel('Y position')

        if return_ax:
            return ax
        else:
            return

    def plot_plan(self, ax=None, **kwargs):
        """
        Make a map-like plot of the well trajectory.

        TODO
        - Use cartopy or similar for this.
        """
        rng_x = max(self.position[:, 0]) - min(self.position[:, 0])
        rng_y = max(self.position[:, 1]) - min(self.position[:, 1])
        max_pos = np.argmax([rng_x, rng_y])

        if max_pos == 0:
            figsize = (10, 10*rng_y/rng_x)
        else:
            figsize = (10*rng_x/rng_y, 10)

        return_ax = True
        if ax is None:
            fig, ax = plt.subplots(figsize=figsize)
            return_ax = False

        ax.plot(*self.trajectory()[:, :2].T, **kwargs)
        ax.grid(color='black', alpha=0.2)
        ax.set_xlabel('X position')
        ax.set_ylabel('Y position')

        if return_ax:
            return ax
        else:
            return
