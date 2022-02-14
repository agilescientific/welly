"""
Defines well location.

:copyright: 2021 Agile Geoscience
:license: Apache 2.0
"""
import warnings
import re
import io

import numpy as np
from scipy.interpolate import interp1d
from scipy.interpolate import splprep
from scipy.interpolate import splev
import matplotlib.pyplot as plt

from . import utils
from .fields import las_fields
from .fields import dev_fields
from .crs import CRS
from .tools import compute_position_log


class Location(object):
    """
    Contains all location and spatial information.
    """
    def __init__(self, params=None):
        self.position = None
        self.crs = CRS()

        if params is None:
            params = {}

        for k, v in params.items():
            if k and (v is not None):
                if k.lower() == 'crs':
                    setattr(self, 'crs', CRS(v))
                    continue
                try:
                    v_ = float(v.replace(',', ''))
                    if not np.isinf(v_):
                        setattr(self, k, v_)
                    else:
                        setattr(self, k, v)
                except:
                    if v in ['None', 'none', 'NONE']:
                        v = None
                    setattr(self, k, v)

        td = getattr(self,
                     'td',
                     getattr(self, 'TDD', getattr(self, 'TDL', None))
                     )
        if isinstance(td, str):
            try:
                td = float(td)
            except ValueError:
                td = None
        self.td = td

        if getattr(self, 'deviation', None) is None:
            self.deviation = None
        else:
            dev_new, pos, dog = compute_position_log(self.deviation, td=td)
            self.position = pos
            self.dogleg = dog

        return

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
    def from_lasio(cls, header, remap=None, funcs=None):
        """
        Make a Location object from a header object.
        See `las.from_las()` for header object description.

        Args:
            header (pd.DataFrame). Header meta data from LAS file
            remap (dict): Optional. A dict of 'old': 'new' LAS field names.
            funcs (dict): Optional. A dict of 'las field': function() for
                implementing a transform before loading. Can be a lambda.

        Returns:
            Location. An instance of this class.
        """
        params = {}
        funcs = funcs or {}
        funcs['location'] = str
        for field, (sect, item) in las_fields['location'].items():
            params[field] = utils.get_header_item(header,
                                                  section=sect,
                                                  item=item,
                                                  remap=remap,
                                                  funcs=funcs)
        return cls(params)

    @classmethod
    def from_petrel(cls,
                    fname,
                    recalc=False,
                    north='grid',
                    columns=None,
                    update=True,
                    **kwargs
                    ):
        """
        Add a location object from a Petrel `dev` file. Should contain the
        (x, y), the CRS, the KB, and the position log.

        Args:
            fname (str): The dev filename.
            recalc (bool): Whether to recalculate the position log from the
                deviation survey (if possible). Default: `False`.
            north (str): Can be 'grid' or 'true'. This is only a preference;
                if only one `AZIM` column is present, you're getting whatever
                it is.
            columns (array): The columns of the dev file holding the data. If
                recalc is False (default), then this will be the indices of
                (x, y, TVDSS), in that order and zero-indexed. Default in that
                case: `[1, 2, 3]`. However, if `recalc` is True then this will
                be the indices of the dev file columns giving (MD, INCL, AZIM),
                in that order. In this case the default is `[0, 8, 10]` for
                'grid' north, or `[0, 8, 7]` for 'true' north.
            update: This function makes some adjustments to the position or
                deviation data, to account for the surface and TD. If you don't
                want to change the data from the file, set to False. (The
                Petrel file probably has absolute position, whereas `welly`
                computes relative position, so the first row is always
                (0, 0, 0). Also, `welly` always adds points for the 3D position
                of TD and KB.)
            **kwargs: passed to `welly.tools.compute_position_log`.

        Returns:
            Location. An instance of this class.
        """
        with open(fname, 'rt') as f:
            text = f.read()

        # Get data from header.
        params = {}
        for field, (pattern, func) in dev_fields.items():
            try:
                value = re.search(pattern, text).groups()[0]
            except:
                value = np.nan
            params[field] = func(value)

        # Find end of header, which ends in row of '=' signs.
        data = io.StringIO(text[text.rfind('=')+2:])

        if recalc:
            if columns is None:
                columns = [0, 8, 10] if north == 'grid' else [0, 8, 7]
            deviation = np.genfromtxt(data)[:, columns]
            dev_new, pos, dog = compute_position_log(deviation, **kwargs)

            if update:
                params['deviation'] = dev_new
            else:
                params['deviation'] = deviation
            params['position'] = pos
            params['dogleg'] = dog

        else:
            if columns is None:
                columns = [1, 2, 3]
            position = np.genfromtxt(data)[:, columns]
            try:
                rel_pos = np.array([params['x'], params['y'], params['kb']])
                pos_new = position - rel_pos
            except KeyError:
                m = "The position log could not be adjusted to relative "
                m += "position; leaving it as-is. Take care to check it."
                warnings.warn(m)
                pos_new = position
            if update:
                params['position'] = pos_new
            else:
                params['position'] = position

        return cls(params)

    def add_deviation(self,
                      deviation,
                      td=None,
                      method='mc',
                      update_deviation=True,
                      azimuth_datum=0,
                      course_length=30,
                      ):
        """
        Add a deviation survey to this instance, and try to compute a position
        log from it. Acts in place, modifying the Location instance directly.

        Args:
            deviation (array): The columns should be: MD, INCL, AZI.
            td (Number): The TD of the well, if not the end of the deviation
                survey you're passing.
            method (str):
                'aa': average angle
                'bt': balanced tangential
                'mc': minimum curvature
            update_deviation: This function makes some adjustments to the dev-
                iation survey, to account for the surface and TD. If you do not
                want to change the stored deviation survey, set to False.
            azimuth_datum (float): The orientation of the azimuth datum,
                relative to the y-axis.
            course_length (float): The length over which to normalize the dogleg
                severity. Typical values are 30 m or 100 ft. Use 1 for no normal-
                ization.

        Returns:
            None. Adds the position log to `well.location` in place.
        """
        dev_new, pos, dog = compute_position_log(deviation,
                                                 td,
                                                 method,
                                                 azimuth_datum,
                                                 course_length,
                                                 )

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

    def trajectory(self, datum=None, elev=True, points=1000, **kwargs):
        """
        Get regularly sampled well trajectory. Assumes there is a position
        log already, e.g. resulting from calling `add_deviation()` on a
        deviation survey.

        Args:
            datum (array-like): A 3-element array with adjustments to
                (x, y, z). For example, the x-position, y-position, and KB of
                the tophole location.
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

        if pos.shape[0] <= 3:
            k = pos.shape[0] - 1
        else:
            k = 3

        # Compute the spline and return as an array instead of as vectors.
        knees, _ = splprep(pos.T, k=k, **kwargs)
        spline = splev(np.linspace(0, 1, points), knees)
        return np.array(spline).T

    def plot_3d(self, ax=None, **kwargs):
        """
        Make a 3D plot of the well trajectory.
        """
        return_ax = True
        if ax is None:
            subplot_kw = {'projection': '3d'}
            fig, ax = plt.subplots(figsize=(15, 7), subplot_kw=subplot_kw)
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
