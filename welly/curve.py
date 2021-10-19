import numpy as np
import pandas as pd

from welly.plot import plot_2d_curve, plot_curve, plot_kde_curve
from welly.quality import quality_score_curve, qflags_curve, quality_curve, \
    qflag_curve
from welly.utils import get_step_from_array


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

        # construct dataframe
        self.df = pd.DataFrame(data=data, index=index, dtype=dtype)

        if type(mnemonic) == str:
            mnemonic = [mnemonic]

        # set mnemonic(s) as column name(s)
        self.df.columns = mnemonic

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
