import copy

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

from welly.plot import plot_2d_curve, plot_curve, plot_kde_curve
from welly.quality import quality_score_curve, qflags_curve, quality_curve, \
    qflag_curve
from welly.utils import get_step_from_array
from . import utils


class Curve(object):
    """
    Curve object that can hold 1D and 2D categorical/numerical curve data.
    Args:
        data (ndarray, Iterable, dict, or pd.DataFrame):
            1D/2D/3D curve numerical or categorical data. Dict can contain
            Series, arrays, constants, dataclass or list-like objects. If
            data is a dict, column order follows insertion-order. Input is
            passed as 'data' argument of pd.DataFrame constructor.
        index (Index or array-like): Optional.
            Index to use for resulting pd.DataFrame. Will default to
            RangeIndex if no indexing information part of input data and no
            index provided. Input is passed to 'index' parameter of the
            pd.DataFrame constructor.
        mnemonic (list or str): Optional.
            The mnemonic(s) of the curve if the data does not have them. It is
            passed as the 'columns' parameter of pd.DataFrame constructor.
            Single mnemonic for 1D data, multiple mnemnonics for 2D data.
        dtype (str): Optional.
            Data type to force. Only a single dtype is allowed. If None,
            infer. Passed to pd.DataFrame constructor.
        index_name (str): Optional.
            Name of the index that will be assigned to
            pd.DataFrame.index.name (e.g. 'depth', 'time').
        index_unit (str): Optional.
            Unit of the index (e.g. 'ft', 'm', 'ms').
        api (str): Optional.
            Application program interface number.
        code (int): Optional.
            Log code
        date (str): Optional.
            Date of when the curve was recorded, interpreted or exported.
        description (str): Optional.
            Description of the curve.
        null (float): Optional.
            Numeric null value representation (e.g. -9999).
        run (int): Optional.
            The count of the run of the same measurement through the same well.
        service_company (str): Optional.
            Company that executed logging operations.
        units (str): Optional.
            Units of the curve measurements.
        Returns:
            curve (welly.Curve): The curve object.
    """
    def __init__(self,
                 data,
                 index=None,
                 mnemonic=None,
                 dtype=None,
                 index_name=None,
                 index_unit=None,
                 api=None,
                 code=None,
                 description=None,
                 date=None,
                 null=None,
                 run=None,
                 service_company=None,
                 units=None):

        if type(mnemonic) == str:
            mnemonic = [mnemonic]

        if isinstance(data, pd.DataFrame):
            self.df = data
            if mnemonic:
                self.df.columns = mnemonic
        else:
            # construct dataframe
            self.df = pd.DataFrame(data=data, index=index, dtype=dtype, columns=mnemonic)

        if index_name:
            self.df.index.name = index_name

        # set parameters related to curve
        self.index_unit = index_unit
        self.code = code
        self.description = description
        self.units = units
        # set parameters related to well
        self.api = api
        self.date = date
        self.null = null
        self.run = run
        self.service_company = service_company

    def __str__(self) -> str:
        """
        A more useful and comprehensive string representation of the Curve.
        Access through calling `print(curve_object)`.
        Arguments:
            No arguments
        Return:
            String representation of:
            - the class name
            - the pd.DataFrame if ncol>1 and the pd.Series if ncol==1
            - the attributes that are attached to the object and that exist
        """
        params = {
            'api': self.api,
            'code': self.code,
            'date': self.date,
            'description': self.description,
            'index_unit': self.index_unit,
            'null': self.null,
            'run': self.run,
            'service_company': self.service_company,
            'start': self.start,
            'step': self.step,
            'stop': self.stop,
            'unit': self.units
        }

        # remove items where item value is None
        params = {k: v for k, v in params.items() if v is not None}

        # show the pd.Series if pd.DataFrame has only 1 column (1D data)
        if self.df.shape[1] == 1:
            show_df = self.df.iloc[:, 0]
        else:
            show_df = self.df

        return '%s \n%s \n attributes: \n  %s' % (self.__class__, show_df, params)

    @property
    def index(self):
        return self.df.index

    @property
    def mnemonic(self):
        """
        Return the mnemonic. For a 1d curve, the mnemonic is a string.
        For a multiple dimension curve, the mnemonic is a list.
        """
        mnemonic = self.df.columns
        if len(mnemonic) == 1:
            mnemonic = mnemonic[0]

        return mnemonic

    @property
    def dtype(self):
        return self.df.dtypes

    @property
    def index_name(self):
        if isinstance(self.df.index, pd.MultiIndex):
            return self.df.index.names
        else:
            return self.df.index.name

    @property
    def start(self):
        """
        The value of the first index. Requires the df (pd.DataFrame) to exist.
        We keep track of this property because start (STRT) is a required field
        in a LAS file.
        """
        return self.df.index[0]

    @property
    def stop(self):
        """
        The value of the last index.
        We keep track of this property because stop (STOP) is a required field
        in a LAS file.
        """
        return self.df.index[-1]

    @property
    def step(self):
        """
        The increment of the index. Requires a numeric index.
        We keep track of this property because step (STEP) is a required field
        in a LAS file.
        Returns:
            Float. If the index is numeric and equally sampled
            0. If the index is numeric and not equally sampled
            None. If the index is not numeric
        """
        if self.df.index.is_numeric():
            return get_step_from_array(self.df.index.values)
        else:
            return None

    @property
    def basis(self):
        """
        The depth or time basis of the curve's points. Computed
        on the fly from the start, stop and step.

        Returns
            ndarray. The array, the same length as the curve.
        """
        return np.linspace(self.start, self.stop, self.df.__len__(), endpoint=True)

    def get_alias(self, alias):
        """
        Given a mnemonic, get the alias name(s) it falls under. If there aren't
        any, you get an empty list.
        """
        alias = alias or {}

        # 1-dimensional curve
        if self.df.columns.__len__() == 1:
            return [k for k, v in alias.items() if self.mnemonic in v]
        # Multi-dimensional curve
        elif self.df.columns.__len__() >= 2:
            alias_list = []
            for mnemonic in self.mnemonic:
                alias_list += [k for k, v in alias.items() if mnemonic.replace('[0]', '') in v]
            return alias_list
        # Data is empty
        else:
            return []

    def as_numpy(self):
        """
        Return only the numeric columns as numpy array
        """
        numerics = ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']
        numeric_df = self.df.select_dtypes(include=numerics)
        if numeric_df.columns.__len__() == 1:
            return numeric_df.iloc[:, 0].values
        else:
            return numeric_df.values

    def _rolling_window(self, window_length, func1d, step=1, return_rolled=False):
        """
        Private function. Smoother for other smoothing/conditioning functions.
        Treat Curve data as numpy array.

        Args:
            window_length (int): the window length.
            func1d (function): a function that takes a 1D array and returns a
                scalar.
            step (int): if you want to skip samples in the shifted versions.
                Don't use this for smoothing, you will get strange results.

        Returns:
            ndarray: the resulting array.
        """
        # Force odd.
        if window_length % 2 == 0:
            window_length += 1

        curve_data = self.as_numpy()

        shape = curve_data.shape[:-1] + (curve_data.shape[-1], window_length)
        strides = curve_data.strides + (step * curve_data.strides[-1],)
        data = np.nan_to_num(curve_data)

        data = np.pad(data, int(step * window_length // 2), mode='edge')
        rolled = np.lib.stride_tricks.as_strided(data,
                                                 shape=shape,
                                                 strides=strides)
        result = np.apply_along_axis(func1d, -1, rolled)
        result[np.isnan(curve_data)] = np.nan

        if return_rolled:
            return result, rolled
        else:
            return result

    def despike(self, window_length=33, samples=True, z=2):
        """
        Args:
            window (int): window length in samples. Default 33 (or 5 m for
                most curves sampled at 0.1524 m intervals).
            samples (bool): window length is in samples. Use False for a window
                length given in metres.
            z (float): Z score

        Returns:
            Curve.
        """
        curve_value = self.as_numpy()

        window_length //= 1 if samples else self.step
        z *= np.nanstd(curve_value)  # Transform to curve's units
        curve_sm = self._rolling_window(window_length, np.median)
        spikes = np.where(np.nan_to_num(curve_value - curve_sm) > z)[0]
        spukes = np.where(np.nan_to_num(curve_sm - curve_value) > z)[0]
        out = np.copy(curve_value)
        out[spikes] = curve_sm[spikes] + z
        out[spukes] = curve_sm[spukes] - z

        copied_curve = copy.deepcopy(self)
        copied_curve.df.iloc[:, 0] = out
        return copied_curve

    def apply(self, window_length, samples=True, func1d=None):
        """
        Runs any kind of function over a window. Only works on a 1d Curve.

        Args:
            window_length (int): the window length. Required.
            samples (bool): window length is in samples. Use False for a window
                length given in metres.
            func1d (function): a function that takes a 1D array and returns a
                scalar. Default: ``np.mean()``.

        Returns:
            Curve.
        """
        window_length /= 1 if samples else self.step
        if func1d is None:
            func1d = np.mean
        out = self._rolling_window(int(window_length), func1d)
        copied_curve = copy.deepcopy(self)
        copied_curve.df.iloc[:, 0] = out

        return copied_curve

    def plot_2d(self,
                ax=None,
                width=None,
                aspect=60,
                cmap=None,
                curve=False,
                ticks=(1, 10),
                return_fig=False,
                **kwargs):
        """
        Plot a 2D curve. Wrapping plot function from plot.py.
        By default only show the plot, not return the figure object.
        Args:
            ax (ax): A matplotlib axis.
            width (int): The width of the image.
            aspect (int): The aspect ratio (not quantitative at all).
            cmap (str): The colourmap to use.
            curve (bool): Whether to plot the curve as well.
            ticks (tuple): The tick interval on the y-axis.
            return_fig (bool): whether to return the matplotlib figure.
                Default False.
        Returns:
            ax. If you passed in an ax, otherwise None.
        """
        plot_2d_curve(self,
                      ax=ax,
                      width=width,
                      aspect=aspect,
                      cmap=cmap,
                      plot_curve=curve,
                      ticks=ticks,
                      return_fig=return_fig,
                      **kwargs)

    def plot(self, ax=None, legend=None, return_fig=False, **kwargs):
        """
        Plot a curve. Wrapping plot function from plot.py.
        By default only show the plot, not return the figure object.
        Args:
            ax (ax): A matplotlib axis.
            legend (striplog.legend): A legend. Optional. Should contain kwargs for ax.set().
            return_fig (bool): whether to return the matplotlib figure.
                Default False.
            kwargs: Arguments for ``ax.plot()``
        Returns:
            ax. If you passed in an ax, otherwise None.
        """
        return plot_curve(self,
                          ax=ax,
                          legend=legend,
                          return_fig=return_fig,
                          **kwargs)

    def plot_kde(self,
                 ax=None,
                 amax=None,
                 amin=None,
                 label=None,
                 return_fig=False):
        """
        Plot a KDE for the curve. Very nice summary of KDEs:
        https://jakevdp.github.io/blog/2013/12/01/kernel-density-estimation/
        Wrapping plot function from plot.py.
        By default only show the plot, not return the figure object.
        Args:
            ax (axis): Optional matplotlib (MPL) axis to plot into. Returned.
            amax (float): Optional max value to permit.
            amin (float): Optional min value to permit.
            label (string): What to put on the y-axis. Defaults to curve name.
            return_fig (bool): If you want to return the MPL figure object.
        Returns:
            None, axis, figure: depending on what you ask for.
        """
        return plot_kde_curve(self,
                              ax=ax,
                              amax=amax,
                              amin=amin,
                              label=label,
                              return_fig=return_fig)

    def quality(self, tests, alias=None):
        """
        Run a series of tests and return the corresponding results.
        Wrapping function from quality.py
        Args:
            tests (list): a list of functions.
            alias (dict): a dictionary mapping mnemonics to lists of mnemonics.
                e.g. {'density': ['DEN', 'DENS']}
        Returns:
            list. The results. Stick to booleans (True = pass) or ints.
        """
        # Gather the test s.
        # First, anything called 'all', 'All', or 'ALL'.
        # Second, anything with the name of the curve we're in now.
        # Third, anything that the alias list has for this curve.
        # (This requires a reverse look-up so it's a bit messy.)
        return quality_curve(self,
                             tests=tests,
                             alias=alias)

    def quality_score(self, tests, alias=None):
        """
        Wrapping function from quality.py
        Run a series of tests and return the normalized score.
            1.0:   Passed all tests.
            (0-1): Passed a fraction of tests.
            0.0:   Passed no tests.
            -1.0:  Took no tests.
        Args:
            tests (list): a list of functions.
            alias (dict): a dictionary mapping mnemonics to lists of mnemonics.
                e.g. {'density': ['DEN', 'DENS']}
        Returns:
            float. The fraction of tests passed, or -1 for 'took no tests'.
        """
        return quality_score_curve(self,
                                   tests=tests,
                                   alias=alias)

    def qflag(self, tests, alias=None):
        """
        Run a test and return the corresponding results on a sample-by-sample
        basis. Wrapping function from quality.py
        Args:
            tests (list): a list of functions.
            alias (dict): a dictionary mapping mnemonics to lists of mnemonics.
                e.g. {'density': ['DEN', 'DENS']}
        Returns:
            list. The results. Stick to booleans (True = pass) or ints.
        """
        # Gather the tests.
        # First, anything called 'all', 'All', or 'ALL'.
        # Second, anything with the name of the curve we're in now.
        # Third, anything that the alias list has for this curve.
        # (This requires a reverse look-up so it's a bit messy.)
        return qflag_curve(self,
                           tests=tests,
                           alias=alias)

    def qflags(self, tests, alias=None):
        """
        Run a series of tests and return the corresponding results.
        Wrapping function from quality.py
        Args:
            tests (list): a list of functions.
            alias (dict): a dictionary mapping mnemonics to lists of mnemonics.
                e.g. {'density': ['DEN', 'DENS']}
        Returns:
            list. The results. Stick to booleans (True = pass) or ints.
        """
        # Gather the tests.
        # First, anything called 'all', 'All', or 'ALL'.
        # Second, anything with the name of the curve we're in now.
        # Third, anything that the alias list has for this curve.
        # (This requires a reverse look-up so it's a bit messy.)
        return qflags_curve(self,
                            tests=tests,
                            alias=alias)

    def read_at(self, index_value, index_name=None, method='linear'):
        """
        Read the log at a specific depth/time or an array of depths/times.
        If the passed depth/time doesn't exist in the index, interpolate or
        pick the nearest, depending on the passed method. Default is linear
        interpolation.
        Args:
            index_value (float or list of floats): value or values to read from Curve
            index_name (str): Name of the index (e.g. 'DEPTH', 'MD', 'TWT')
            method (str): Optional. Method of interpolation:
                {‘linear’,  ‘pad’/’ffill’, ‘backfill’/’bfill’, ‘nearest’}
        Returns:
            read_value (float or ndarray): The curve value(s) that was read at
                the provided index value(s).
        """
        not_found = False

        if type(index_value) != list:
            index_value = [index_value]

        if not index_name:
            if isinstance(self.df.index, pd.MultiIndex):
                index_name = self.df.index.names[0]
            else:
                index_name = self.df.index.name

        read_values = []

        for value in index_value:
            try:
                # try reading if the passed index value exists
                idx_to_read = self.df.index[self.df.index.get_loc(value)]
                read_values.append(
                    self.df.query(f'{idx_to_read} == {index_name}').values[0][0])
            except KeyError:
                not_found = True

            if not_found:
                if method == 'linear':
                    i, d = utils.find_previous(self.index.values, value,
                                               index=True, return_distance=True)
                    val = utils.linear(self.df.iloc[i, :], self.df.iloc[i+1, :], d).values[0]
                    read_values.append(val)
                else:
                    # if it doesn't exist get previous, next or nearest index
                    idx_to_read = self.df.index[self.df.index.get_loc(value, method)]
                    read_values.append(
                        self.df.query(f'{idx_to_read} == {index_name}').values[0][0])

        if len(read_values) == 1:
            return read_values[0]
        elif len(read_values) > 1:
            return read_values
        else:
            return None

    def to_basis(self,
                 basis=None,
                 start=None,
                 stop=None,
                 step=None,
                 undefined=None,
                 interp_kind='linear'):
        """
        Make a new curve in a new basis, given a basis, or a new start, step,
        and/or stop. You only need to set the parameters you want to change.
        If the new extents go beyond the current extents, the curve is padded
        with the ``undefined`` parameter.
        Args:
            basis (ndarray): The basis to compute values for. You can provide
                a basis, or start, stop, step, or a combination of the two.
            start (float): The start position to use. Overrides the start of
                the basis, if one is provided.
            stop (float): The end position to use. Overrides the end of
                the basis, if one is provided.
            step (float): The step to use. Overrides the step in the basis, if
                one is provided.
            undefined (float): The value to use outside the curve's range. By
                default, np.nan is used.
            interp_kind (str): The kind of interpolation to use to compute the
                new positions, default is 'nearest'. Options are:
                {None, ‘linear‘, backfill’/’bfill’, ‘pad’/’ffill’, ‘nearest’}
        Returns:
            Curve. The current instance in the new basis.
        """
        new_curve = copy.deepcopy(self)

        if basis is None:
            new_start = self.start if start is None else start
            new_stop = self.stop if stop is None else stop
            new_step = self.step if step is None else step
        else:
            new_start = basis[0] if start is None else start
            new_stop = basis[-1] if stop is None else stop
            new_step = (basis[1] - basis[0]) if step is None else step

        steps = np.ceil((new_stop - new_start) / new_step)
        basis = np.linspace(new_start, new_stop, int(steps) + 1, endpoint=True)

        if undefined is None:
            undefined = np.nan
        else:
            undefined = undefined

        if interp_kind == 'linear':
            # set up scipy function for linear interpolation
            interp = interp1d(self.df.index.values,
                              self.df.values[:, 0],
                              kind=interp_kind,
                              bounds_error=False,
                              fill_value=undefined)
            # create new df with interpolated data
            new_df = pd.DataFrame(interp(basis),
                                  index=basis,
                                  columns=self.df.columns)
            # create and set new df attribute on curve
            setattr(new_curve, 'df', new_df)
            # propagate old df attributes to new df curve attribute
            setattr(new_curve.df.index, 'name', self.df.index.name)
            setattr(new_curve.df, 'columns', self.df.columns)
        else:
            new_df = self.df.reindex(index=basis,
                                     method=interp_kind,
                                     fill_value=undefined)
            setattr(new_curve, 'df', new_df)

        return new_curve

    def to_basis_like(self, basis):
        """
        Make a new curve in a new basis, given an existing one. Wraps
        ``to_basis()``.
        Pass in a curve or the basis of a curve.
        Args:
            basis (ndarray): A basis, but can also be a Curve instance.
        Returns:
            Curve. The current instance in the new basis.
        """
        try:  # To treat as a curve.
            curve = basis
            basis = curve.df.index
            undefined = curve.null
        except:
            undefined = None

        return self.to_basis(basis=basis, undefined=undefined)


    def block(self,
              cutoffs=None,
              values=None,
              n_bins=0,
              right=False,
              function=None):
        """
        Block a log based on number of bins, or on cutoffs.
        Args:
            cutoffs (array): the values at which to create the blocks. Pass
                a single number, or an array-like of multiple values. If you
                don't pass `cutoffs`, you should pass `n_bins` (below).
            values (array): the values to map to. Defaults to [0, 1, 2,...].
                There must be one more value than you have `cutoffs` (e.g.
                2 cutoffs will create 3 zones, each of which needs a value).
            n_bins (int): The number of discrete values to use in the blocked
                log. Only used if you don't pass `cutoffs`.
            right (bool): Indicating whether the intervals include the right
                or the left bin edge. Default behavior is `right==False`
                indicating that the interval does not include the right edge.
            function (function): transform the log with a reducing function,
                such as np.mean.
        Returns:
            Curve.
        """
        # We'll return a copy.
        new_curve = copy.deepcopy(self)

        if (values is not None) and (cutoffs is None):
            cutoffs = values[1:]

        if (cutoffs is None) and (n_bins == 0):
            cutoffs = np.mean(self.df.values)

        if (n_bins != 0) and (cutoffs is None):
            mi, ma = np.amin(self.df.values), np.amax(self.df.values)
            cutoffs = np.linspace(mi, ma, n_bins+1)
            cutoffs = cutoffs[:-1]

        try:  # To use cutoff as a list.
            data = np.digitize(self.df.values, cutoffs, right)
        except ValueError:  # It's just a number.
            data = np.digitize(self.df.values, [cutoffs], right)

        if (function is None) and (values is None):
            new_curve.df.iloc[:, :] = data
            return new_curve

        data = data.astype(float)

        # Set the function for reducing.
        f = function or utils.null

        # Find the tops of the 'zones'.
        tops, vals = utils.find_edges(data)

        # End of array trick... adding this should remove the
        # need for the marked lines below. But it doesn't.
        # np.append(tops, None)
        # np.append(vals, None)

        if values is None:
            # Transform each segment in turn, then deal with the last segment.
            for top, base in zip(tops[:-1], tops[1:]):
                data[top:base] = f(np.copy(self.df.values[top:base]))
            data[base:] = f(np.copy(self.df.values[base:]))  # See above
        else:
            for top, base, val in zip(tops[:-1], tops[1:], vals[:-1]):
                data[top:base] = values[int(val)]
            data[base:] = values[int(vals[-1])]  # See above

        new_curve.df.iloc[:, :] = data

        return new_curve