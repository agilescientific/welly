import pandas as pd

from welly.plot import plot_2d_curve, plot_curve, plot_kde_curve
from welly.quality import quality_score_curve, qflags_curve, quality_curve, qflag_curve


class Curve(object):
    """
    Curve object
    """

    def __init__(self,
                 data,
                 index=None,
                 mnemonic=None,
                 dtype=None,
                 api=None,
                 basis_units=None,
                 code=None,
                 description=None,
                 date=None,
                 index_name=None,
                 null=None,
                 run=None,
                 service_company=None,
                 units=None,
                 start=None,
                 stop=None,
                 step=None):
        """
        Args:
            data (ndarray (structured or homogeneous), Iterable, dict, or DataFrame):
                1D/2D curve numerical or categorical data. Dict can contain Series, arrays, constants, dataclass or
                list-like objects. If data is a dict, column order follows insertion-order. Input is passed to 'data'
                parameter of pd.DataFrame constructor.
            index (Index or array-like):
                index to use for resulting pd.DataFrame. Will default to RangeIndex if no indexing information part of
                input data and no index provided. Input is passed to 'index' parameter of the pd.DataFrame constructor.
            mnemonic (str):
                the mnemonic of the curve if the data does not have them. It is passed as the 'columns' param of
                pd.DataFrame constructor.
            dtype (str):
                data type to force. Only a single dtype is allowed. If None, infer. Passed to pd.DataFrame constructor.
            api (str):
                application program interface number.
            basis_units (str):
                unit of the index (e.g. 'ft', 'm', 'ms').
            code (int):
                log code
            date (str):
                date of when the curve was recorded.
            description (str):
                description of the curve.
            index_name (str):
                name of the index that will be assigned to pd.DataFrame.index.name (e.g. 'depth', 'time').
            null (float):
                numeric null value representation (e.g. -9999).
            run (int):
                the count of the run of the same measurement through the same well.
            service_company (str):
                company that executed logging operations.
            start (float):
                index value where index starts
            step (float):
                index value increment
            stop (float):
                index value where index stops
            units (str):
                units of the curve measurements.

        Returns:
            curve (welly.Curve): instance of the Curve object
        """
        self.df = pd.DataFrame(data=data, index=index, dtype=dtype)

        # assign mnemonic to the name of all df columns
        if mnemonic:
            self.df.columns = [mnemonic] * self.df.shape[1]

        if index_name:
            self.df.index.name = index_name

        self.api = api
        self.code = code
        self.date = date
        self.description = description
        self.basis_units = basis_units
        self.null = null
        self.run = run
        self.service_company = service_company
        self.start = start
        self.step = step
        self.stop = stop
        self.units = units

    def __str__(self) -> str:
        params = {
            'api': self.api,
            'code': self.code,
            'date': self.date,
            'description': self.description,
            'basis_units': self.basis_units,
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


@pd.api.extensions.register_dataframe_accessor("curve")
class CurveAccessor:
    """
    Curve accessor that enables custom curve plot and qc functions to be called on the curve df attribute directly
    through the 'curve' namespace.

    Examples of how to use:
        c = Curve(data=[...], mnemonic=[...], ..)
        c.df.curve.plot()
        c.df.curve.quality(tests={'Each': [q.no_flat, q.no_monotonic]})
    """

    def __init__(self, pandas_obj):
        self._obj = pandas_obj

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
        plot_2d_curve(curve=self._obj,
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
        return plot_curve(curve=self._obj,
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
        return plot_kde_curve(curve=self._obj,
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

        Returns:
            list. The results. Stick to booleans (True = pass) or ints.
        """
        # Gather the test s.
        # First, anything called 'all', 'All', or 'ALL'.
        # Second, anything with the name of the curve we're in now.
        # Third, anything that the alias list has for this curve.
        # (This requires a reverse look-up so it's a bit messy.)
        return quality_curve(curve=self._obj,
                             tests=tests,
                             alias=alias)

    def qflag(self, tests, alias=None):
        """
        Run a test and return the corresponding results on a sample-by-sample
        basis. Wrapping function from quality.py

        Args:
            tests (list): a list of functions.
            alias (dict): a dictionary mapping mnemonics to lists of mnemonics.

        Returns:
            list. The results. Stick to booleans (True = pass) or ints.
        """
        # Gather the tests.
        # First, anything called 'all', 'All', or 'ALL'.
        # Second, anything with the name of the curve we're in now.
        # Third, anything that the alias list has for this curve.
        # (This requires a reverse look-up so it's a bit messy.)
        return qflag_curve(curve=self._obj,
                           tests=tests,
                           alias=alias)

    def qflags(self, tests, alias=None):
        """
        Run a series of tests and return the corresponding results.
        Wrapping function from quality.py

        Args:
            tests (list): a list of functions.
            alias (dict): a dictionary mapping mnemonics to lists of mnemonics.

        Returns:
            list. The results. Stick to booleans (True = pass) or ints.
        """
        # Gather the tests.
        # First, anything called 'all', 'All', or 'ALL'.
        # Second, anything with the name of the curve we're in now.
        # Third, anything that the alias list has for this curve.
        # (This requires a reverse look-up so it's a bit messy.)
        return qflags_curve(curve=self._obj,
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

        Returns:
            float. The fraction of tests passed, or -1 for 'took no tests'.
        """
        return quality_score_curve(curve=self._obj,
                                   tests=tests,
                                   alias=alias)