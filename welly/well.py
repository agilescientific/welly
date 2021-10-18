"""
Defines wells.

:copyright: 2021 Agile Scientific
:license: Apache 2.0
"""
from __future__ import division

import re

import numpy as np

import pandas as pd

from . import utils
from .fields import las_fields as LAS_FIELDS
from .curve import Curve
from .las import from_las, file_from_url, from_lasio, to_lasio
from .location import Location
from .synthetic import Synthetic
from .canstrat import well_to_card_1
from .canstrat import well_to_card_2
from .canstrat import interval_to_card_7
from .canstrat import write_row
from .plot import plot_well, plot_depth_track_well
from .quality import qc_data_well, qc_curve_group_well, qc_table_html_well

###############################################
# This module is not used directly, but must
# be imported in order to register new scales.
from . import scales  # DO NOT DELETE
###############################################


# define possible depth/time/index curve mnemonics in a LAS file
index_curve_mnemonics = ['DEPT', 'DEPTH', 'TIME', 'INDEX']


class WellError(Exception):
    """
    Generic error class.
    """
    pass


def _get_well_params(header, remap, funcs):
    """
    Get the well related LAS parameters from the header and remap and/or
    transform the parameters if `remap` dict or transform `funcs` are passed.

    Args:
        header (pd.DataFrame): Header meta data.
            See `las.from_las()` for description.
        remap (dict): Optional. A dict of 'old': 'new' LAS field names.
        funcs (dict): Optional. A dict of 'las field': function() for
            implementing a transform before loading. Can be a lambda.

    Returns:
        well_params (dict): LAS parameters that belong to the well

    """
    # retrieve well parameters from header
    well_params = {}

    for field, (section, item) in LAS_FIELDS['data'].items():
        well_params[field] = utils.get_header_item(header=header,
                                                   section=section,
                                                   item=item,
                                                   remap=remap,
                                                   funcs=funcs)

    return well_params


def _get_curve_params(header, dataset_name):
    """
    Get the curve related LAS parameters from the header.

    For every curve, get the 'mnemonic', 'unit' and 'description'.

    Args:
        header (pd.DataFrame): Header meta data.
            See `las.from_las()` for description.
        dataset_name: The name of the dataset as found in the LAS file. Can be:
            'Curves', 'Log,' 'Core', 'Inclinometry', 'Drilling', 'Tops', 'Test'

    Returns:
        curve_params (pd.DataFrame): LAS parameters that belong to the curve(s)

    """
    # retrieve curves mnemonics, units and descriptions from header
    curve_header = header[(header["section"] == dataset_name)]

    curve_params = curve_header[['mnemonic', 'unit', 'descr']].set_index('mnemonic').T

    return curve_params


def _convert_depth_index_unit(index, unit_from, unit_to):
    """
    Convert a depth index from and to meters and feet. Flip the depth index if
    it is descending because it should be ascending (increasing in depth).
    Return index as a pandas Index object.

    Args:
        index (np.array): The index.
        unit_from (str): The current index unit.
        unit_to (str): The index unit to convert to (e.g. 'm', 'ft').

    Returns:
        index (pd.Index): The converted index
    """
    if (unit_from.lower() == 'm' or unit_from == '') and "ft" in unit_to.lower():
        index = index * 3.280839895  # convert to ft
    elif (unit_from.lower() == 'ft' or unit_from == '') and "m" in unit_to.lower():
        index = index * 0.3048000000012192  # convert to m
    else:
        raise KeyError(f"Index must be 'm' or 'ft', but was: {unit_to}")

    # flip the index if it is descending
    if index[0] > index[1]:
        index = np.flipud(index)

    return pd.Index(index)


def _update_las_header(header, remap=None, funcs=None):
    """
    Helper function that takes a header object, remapping dictionaries and
    transformer functions. Retrieves every header LAS item from the
    dataframe, remaps and/or transforms the item and puts it back in a copy
    of the header dataframe.

    Args:
        header (pd.DataFrame): header meta data. See `las.from_las()` for
            description.
        remap (dict): Optional. A dict of 'old': 'new' LAS field names.
        funcs (dict): Optional. A dict of 'las field': function() for
            implementing a transform before loading. Can be a lambda.

    Returns:
        updated_header (pd.DataFrame): header with remapped and/or
            transformed items, if passed.
    """
    updated_header = header.copy()

    # loop over every header LAS field
    for section, item in LAS_FIELDS['header'].values():
        # remap or transform if remap/funcs is passed
        new_item_value = utils.get_header_item(header=header,
                                               section=section,
                                               item=item,
                                               remap=remap,
                                               funcs=funcs)
        # get row index of field
        row_index = header.index[header['mnemonic'] == item]

        # replace item with new item value
        header.loc[row_index, 'mnemonic'] = new_item_value

    return updated_header


class Well(object):
    """
    Well contains everything about the well.
    """

    def __init__(self, params=None):
        """
        Generic initializer.
        """
        if params is None:
            params = {}

        for k, v in params.items():
            if k and (v is not None):
                setattr(self, k, v)

        self.data = getattr(self, 'data', {})
        self.header = getattr(self, 'header', pd.DataFrame())
        self.location = getattr(self, 'location', Location())

    def __eq__(self, other):
        if (not self.uwi) or (not other.uwi):
            m = "One or both UWIs is blank, cannot determine equality."
            raise WellError(m)
        if self.uwi == other.uwi:
            return True
        return False

    def __bool__(self):
        """
        Truthiness.
        """
        if self.header is not None or self.data is not None or self.uwi:
            return True
        return False

    __nonzero__ = __bool__  # Python 2.7.

    def __repr__(self):
        """
        Non-rich representation.
        """
        return "Well(uwi: '{}', {} curves: {})".format(self.uwi,
                                                       len(self.data),
                                                       list(self.data.keys()))

    def _repr_html_(self):
        """
        Jupyter Notebook magic repr function.
        """
        row1 = '<tr><th style="text-align:center;" '
        row1 += 'colspan="2">{}<br><small>{{}}</small></th></tr>'
        rows = row1.format(getattr(self, 'name', ''))
        rows = rows.format(getattr(self, 'uwi', ''))
        s = '<tr><td><strong>{k}</strong></td><td>{v}</td></tr>'

        if getattr(self, 'location', None) is not None:
            for k, v in self.location.__dict__.items():
                if k in ['deviation', 'position']:
                    continue
                if k == 'crs':
                    v = v.__repr__()
                rows += s.format(k=k, v=v)

        if getattr(self, 'data', None) is not None:
            v = ', '.join(sorted(list(self.data.keys())))
            rows += s.format(k="data", v=v)

        html = '<table>{}</table>'.format(rows)
        return html

    @property
    def uwi(self):
        """
        Property. Simply a shortcut to the UWI from the header, or the
        empty string if there isn't one.
        """
        if self.header is not None:
            try:
                return self.header[self.header.mnemonic == 'UWI'].value.iloc[0]
            except IndexError:
                return ''
        else:
            return ''

    @property
    def name(self):
        """
        Property. Simply a shortcut to the well name from the header, or the
        empty string if there isn't one.
        """
        if self.header is not None:
            try:
                return self.header[self.header.mnemonic == 'WELL'].value.iloc[
                    0]
            except IndexError:
                return ''
        else:
            return ''

    def _get_curve_mnemonics(self, keys=None, alias=None, curves_only=True):
        """
        Get mnemonics for entries in `data`. By default, only gets curves.
        If `keys` is a list-like of mnemonics, or list of lists (such as might
        be used to plot tracks), then only get those (ignores anything that is
        not a Curve).
        """
        if keys is None:
            keys_ = self.data.keys()
        elif not keys:
            keys_ = []
        else:
            keys_ = utils.flatten_list(keys)

        if curves_only:
            keys = [k for k in keys_ if
                    isinstance(self.get_curve(k, alias=alias), Curve)]
        else:
            keys = [k for k in keys_ if k in self.data]

        return keys

    @classmethod
    def from_lasio(cls,
                   las,
                   remap=None,
                   funcs=None,
                   data=True,
                   req=None,
                   alias=None,
                   fname=None,
                   index=None):
        """
        Constructor. If you already have the lasio object, then this makes a
        well object from it.

        Args:
            las (lasio.LASFile object): a lasio representation of a LAS file.
            remap (dict): Optional. A dict of 'old': 'new' LAS field names.
            funcs (dict): Optional. A dict of 'las field': function() for
                implementing a transform before loading. Can be a lambda.
            data (bool): Whether to load curves or not.
            req (list): An alias list, giving all required curves.
            alias (dict): An alias dictionary.
            fname (str): The filename, if you want to keep it.
            index (str): Optional. Either "existing" (use the index as found in
                the LAS file) or "m", "ft" to use lasio's conversion of the
                relevant index unit.

        Returns:
            well (welly.Well). The well object.
        """
        datasets = from_lasio(las)

        well = cls.from_datasets(datasets,
                                 remap=remap,
                                 funcs=funcs,
                                 data=data,
                                 req=req,
                                 alias=alias,
                                 fname=fname,
                                 index_unit=index)

        return well

    @classmethod
    def from_las(cls,
                 fname,
                 remap=None,
                 funcs=None,
                 data=True,
                 req=None,
                 alias=None,
                 encoding=None,
                 printfname=False,
                 index=None):
        """
        Constructor. If you have a LAS file saved on disk, this creates a well
        object from it.

        Args:
            fname (str or pathlib.Path): The path of the LAS file, or a URL to
                one.
            remap (dict): Optional. A dict of 'old': 'new' LAS field names.
            funcs (dict): Optional. A dict of 'las field': function() for
                implementing a transform before loading. Can be a lambda.
            data (bool): Optional. Whether to load the data or only the header.
            req (list): Optional. An alias list, giving all required curves.
            alias (dict): Optional. An alias dictionary.
            encoding (str): Optional. the character encoding used when reading
                the LAS file in from disk.
            printfname (bool): Optional. prints filename before trying to load
                it, for debugging.
            index (str): Optional. Either "existing" (use the index as found in
                the LAS file) or "m", "ft" to use lasio's conversion of the
                relevant index unit.

        Returns:
            well. The well object.
        """
        fname = utils.to_filename(fname)

        if printfname:
            print(fname)

        # if https URL is passed try reading and formatting it to text file
        if re.match(r'https?://.+\..+/.+?', fname) is not None:
            fname = file_from_url(fname)

        datasets = from_las(fname, encoding=encoding)

        # create well from datasets
        well = cls.from_datasets(datasets,
                                 remap=remap,
                                 funcs=funcs,
                                 data=data,
                                 req=req,
                                 alias=alias,
                                 fname=fname,
                                 index_unit=index)

        return well

    @classmethod
    def from_datasets(cls,
                      datasets,
                      remap=None,
                      funcs=None,
                      data=None,
                      req=None,
                      alias=None,
                      fname=None,
                      index_unit=None):
        """
        Constructor. If you have `datasets`, this will create a well object
        from it. See :func:`las.from_las()` for a description of a `datasets`
        object.

        This method requires:
            - first column of `data` to be the Index/Depth/Time Curve
            - TODO: Complete requirements

        Args:
            datasets (Dict['name': (data (DataFrame), header (DataFrame))]):
                A dictionary that maps the 'dataset name' to a tuple of a
                header and data pd.DataFrames.
            remap (dict): Optional. A dict of 'old': 'new' LAS field names.
            funcs (dict): Optional. A dict of 'las field': function() for
                implementing a transform before loading. Can be a lambda.
            data (bool): Whether to load curves or not.
            req (list): An alias list, giving all required curves.
            alias (dict): An alias dictionary.
            fname (str): The filename, if you want to keep it.
            index_unit (str): Optional. The unit of the index upon construction
                of the Curves (e.g. 'm' or 'ft'). Will perform unit conversion
                if specified index unit is different than the existing index
                unit.

        Returns:
            well (welly.Well). The well object.
        """
        # unpack datasets
        for dataset_name, (df_data, df_header) in datasets.items():

            # get the well related parameters
            well_params = _get_well_params(df_header, remap, funcs)

            # get the time/depth index, LAS requires it to be the first curve
            index = df_data.iloc[:, 0].values

            # get index unit from the first curve
            unit = df_header[(df_header["section"] == dataset_name)].iloc[0].unit

            if index_unit:
                # convert index to different index unit, if passed
                index = _convert_depth_index_unit(index=index,
                                                  unit_from=unit,
                                                  unit_to=index_unit)
                # set to the unit that the index has just been converted to
                unit = index_unit

            well_params['index_unit'] = unit

            # get the curve related parameters (mnemonic, unit, description)
            curve_params = _get_curve_params(df_header, dataset_name)

            # update header with remapped and transformed items, if passed
            updated_df_header = _update_las_header(df_header, remap, funcs)

            if req and alias:
                req = utils.flatten_list([v for k, v in alias.items() if k in req])

            if data and req:
                curves = {mnemonic: Curve(data=df_data[mnemonic],
                                          mnemonic=mnemonic,
                                          units=curve_params[mnemonic].unit,
                                          description=curve_params[mnemonic].descr,
                                          index=index,
                                          **well_params)
                          for mnemonic in df_data.columns if (mnemonic[:4] not in index_curve_mnemonics) and (mnemonic in req)}
            elif data and not req:
                curves = {mnemonic: Curve(data=df_data[mnemonic],
                                          mnemonic=mnemonic,
                                          units=curve_params[mnemonic].unit,
                                          description=curve_params[mnemonic].descr,
                                          index=index,
                                          **well_params)
                          for mnemonic in df_data.columns if (mnemonic[:4] not in index_curve_mnemonics)}
            elif (not data) and req:
                curves = {mnemonic: True for mnemonic in df_data.columns
                          if (mnemonic[:4] not in index_curve_mnemonics)
                          and (mnemonic in req)}
            else:
                curves = {mnemonic: True for mnemonic in df_data.columns
                          if (mnemonic[:4] not in index_curve_mnemonics)}

            if req:
                aliases = utils.flatten_list([c.get_alias(alias) for mnemonic, c in curves.items()])
                if len(set(aliases)) < len(req):
                    return cls(params={})

            # build a dict of the well properties
            params = {'las': df_data,
                      'header': updated_df_header,
                      'location': Location.from_lasio(df_header,
                                                      remap=remap,
                                                      funcs=funcs),
                      'data': curves,
                      'fname': fname}

            return cls(params)

    def to_lasio(self, keys=None, alias=None, basis=None, null_value=-999.25):
        """
        Makes a lasio object from the current well.

        Args:
            keys (list): List of strings: the keys of the data items to
                include, if not all of them. You can have nested lists, such
                as you might use for ``tracks`` in ``well.plot()``.
            alias (dict): Optional. A dictionary alias for the curve mnemonics.
            basis (numpy.ndarray): Optional. The basis to export the curves in.
                If you don't specify one, it will survey all the curves with
                `survey_basis()``.
            null_value (float): Optional. The null value representation in the LAS file.

        Returns:
            las (lasio.LASFile). The lasio object representation of a LAS file.
        """
        las = to_lasio(self, keys, alias, basis, null_value)

        return las

    def to_las(self,
               fname,
               keys=None,
               basis=None,
               null_value=-999.25,
               **kwargs):
        """
        Writes the current well instance as a LAS file. Essentially just wraps
        ``to_lasio()``, but is more convenient for most purposes.

        Args:
            fname (str): The path of the LAS file to create.
            basis (ndarray): Optional. The basis to export the curves in. If
                you don't specify one, it will survey all the curves with
                ``survey_basis()``.
            null_value (float): Optional. numeric null value representation
            keys (list): List of strings: the keys of the data items to
                include, if not all of them. You can have nested lists, such
                as you might use for ``tracks`` in ``well.plot()``.

        Other keyword Args are passed to ``lasio.LASFile.write()``.

        Returns:
            None. Writes the file as a side-effect.
        """
        with open(fname, 'w') as f:
            las = self.to_lasio(keys=keys, basis=basis, null_value=null_value)
            las.write(f, **kwargs)

    def to_datasets(self):
        """

        """
        # TODO
        #   implement after refactoring of Curve object
        pass

    def df(self,
           keys=None,
           basis=None,
           uwi=False,
           alias=None,
           rename_aliased=True):
        """
        Return current curve data as a ``pandas.DataFrame`` object.

        Requires `pandas`.

        Everything has to have the same basis, because the depth
        is going to become the index of the DataFrame. If you don't
        provide one, ``welly`` will make one using ``survey_basis()``.

        Args:
            keys (list): List of strings: the keys of the data items to
                survey, if not all of them.
            basis (array): A basis, if you want to enforce one, otherwise
                you'll get the result of ``survey_basis()``.
            uwi (bool): Whether to add a 'UWI' column.
            alias (dict): Alias dictionary.
            rename_aliased (bool): Whether to name the columns after the alias,
                i.e. the alias dictionary key, or after the curve mnemonic.
                Default is True, use the alias names.

        Returns:
            pandas.DataFrame.
        """
        try:
            import pandas as pd
        except ModuleNotFoundError:
            m = "You must install pandas to use dataframes."
            raise WellError(m)

        from pandas.api.types import is_object_dtype

        keys = self._get_curve_mnemonics(keys, alias=alias)

        data = {k: self.get_curve(k, alias=alias) for k in keys}

        if basis is None:
            basis = self.survey_basis(keys=keys, alias=alias)
        if basis is None:
            m = "No basis was provided and welly could not retrieve common basis."
            raise WellError(m)

        df = pd.DataFrame(data, index=None)
        df['Depth'] = basis
        df = df.set_index('Depth')

        if not rename_aliased:
            mapper = {k: self.get_mnemonic(k, alias=alias) for k in keys}
            df = df.rename(columns=mapper)

        if uwi:
            df['UWI'] = [self.uwi for _ in basis]
            df = df.reset_index()
            df = df.set_index(['UWI', 'Depth'])

        for column in df.columns:
            if is_object_dtype(df[column].dtype):
                try:
                    df[column] = df[column].astype(np.float64)
                except ValueError:
                    pass

        return df

    def add_curves_from_las(self, fname, remap=None, funcs=None):
        """
        Given a LAS file, add curves from it to the current well instance.
        Essentially just wraps ``add_curves_from_lasio()``.

        Args:
            fname (str): The path of the LAS file to read curves from.
            remap (dict): Optional. A dict of 'old': 'new' LAS field names.
            funcs (dict): Optional. A dict of 'las field': function() for
                implementing a transform before loading. Can be a lambda.

        Returns:
            None. Works in place.
        """
        try:  # To treat as a single file
            self.add_curves_from_lasio(from_las(fname), remap=remap,
                                       funcs=funcs)
        except AttributeError:  # It's a list!
            for f in fname:
                self.add_curves_from_lasio(from_las(f), remap=remap,
                                           funcs=funcs)

        return None

    def add_curves_from_lasio(self, datasets, remap=None, funcs=None):
        """
        Given a LAS file, add curves from it to the current well instance.
        Essentially just wraps ``add_curves_from_lasio()``.

        Args:
            datasets (dict): Datasets with curves and headers.
            remap (dict): Optional. A dict of 'old': 'new' LAS field names.
            funcs (dict): Optional. A dict of 'las field': function() for
                implementing a transform before loading. Can be a lambda.

        Returns:
            None. Works in place.
        """
        for name, (df_data, df_header) in datasets.items():
            params = {}
            for field, (sect, code) in LAS_FIELDS['data'].items():
                params[field] = utils.get_header_item(df_header, sect, code,
                                                      remap=remap, funcs=funcs)

            curve_units = df_header[(df_header["section"] == name)][
                ['mnemonic', 'unit', 'descr']].set_index('mnemonic').T

            curves = {mnemonic: Curve.from_lasio_curve(
                curve=df_data[mnemonic].values, mnemonic=mnemonic,
                unit=curve_units[mnemonic].unit,
                description=curve_units[mnemonic].descr, **params) for mnemonic
                in df_data.columns}

            # This will clobber anything with the same key!
            self.data.update(curves)

        return None

    def _plot_depth_track(self, ax, md, kind='MD', tick_spacing=100):
        """
        Private function. Depth track plotting.
        Wrapping plot function from plot.py.

        Args:
            ax (ax): A matplotlib axis.
            md (ndarray): The measured depths of the track.
            kind (str): The kind of track to plot.

        Returns:
            ax.
        """
        return plot_depth_track_well(well=self, ax=ax, md=md, kind=kind,
                                     tick_spacing=tick_spacing)

    def plot(self,
             legend=None,
             tracks=None,
             track_titles=None,
             alias=None,
             basis=None,
             return_fig=False,
             extents='td',
             **kwargs):
        """
        Plot multiple tracks. Wrapping plot function from plot.py.
        By default only show the plot, not return the figure object.

        Args:
            legend (striplog.legend): A legend instance.
            tracks (list): A list of strings and/or lists of strings. The
                tracks you want to plot from ``data``. Optional, but you will
                usually want to give it.
            track_titles (list): Optional. A list of strings and/or lists of
                strings. The names to give the tracks, if you don't want welly
                to guess.
            alias (dict): a dictionary mapping mnemonics to lists of mnemonics.
            basis (ndarray): Optional. The basis of the plot, if you don't
                want welly to guess (probably the best idea).
            return_fig (bool): Whether to return the matplotlig figure. Default
                False.
            extents (str): What to use for the y limits:
                'td' — plot 0 to TD.
                'curves' — use a basis that accommodates all the curves.
                'all' — use a basis that accommodates everything.
                (tuple) — give the upper and lower explictly.

        Returns:
            None. The plot is a side-effect.
        """
        return plot_well(well=self,
                         legend=legend,
                         tracks=tracks,
                         track_titles=track_titles,
                         alias=alias,
                         basis=basis,
                         return_fig=return_fig,
                         extents=extents,
                         **kwargs)

    def coverage(self, keys=None, alias=None):
        """
        Plot the coverage of the curves in a well.
        """
        raise NotImplementedError("Coverage is not implemented yet.")

    def survey_basis(self, keys=None, alias=None, step=None):
        """
        Look at the basis of all the curves in ``well.data`` and return a
        basis with the minimum start, maximum depth, and minimum step.

        Args:
            keys (list): List of strings: the keys of the data items to
                survey, if not all of them.
            alias (dict): a dictionary mapping mnemonics to lists of mnemonics.
            step (float): a new step, if you want to change it.

        Returns:
            ndarray. The most complete common basis.
        """
        keys = self._get_curve_mnemonics(keys, alias=alias)

        starts, stops, steps = [], [], []
        for k in keys:
            d = self.get_curve(k, alias=alias)
            if keys and (d is None):
                continue
            try:
                starts.append(d.basis[0])
                stops.append(d.basis[-1])
                steps.append(d.basis[1] - d.basis[0])
            except Exception as e:
                pass
        if starts and stops and steps:
            step = step or min(steps)
            return np.arange(min(starts), max(stops) + 1e-9, step)
        else:
            return None

    def unify_basis(self, keys=None, alias=None, basis=None, start=None,
                    stop=None, step=None):
        """
        Give every Curve in the well, or everything in the list of keys, the
        same basis. If you don't provide a basis, welly will try to get one
        using ``survey_basis()``.

        Args:
            keys (list): List of strings: the keys of the data items to
                unify, if not all of them.
            alias (dict): an alias dictionary, mapping mnemonics to lists of
                mnemonics.
            basis (ndarray): A basis: the regularly sampled depths at which
                you want the samples.
            start (float): Optionally override the start of whatever basis
                you provide or is surveyed.
            stop (float): Optionally override the stop of whatever basis
                you provide or is surveyed.
            step (float): Optionally override the step in the basis.

        Returns:
            None. Works in place.
        """
        keys = self._get_curve_mnemonics(keys, alias=alias)

        if basis is None:
            basis = self.survey_basis(keys=keys, alias=alias)
        if basis is None:
            m = "No basis was provided and welly could not retrieve common basis."
            raise WellError(m)

        for k in keys:
            if keys and (k not in keys):
                continue
            try:  # To treat as a curve.
                self.data[k] = self.data[k].to_basis(basis, start=start,
                                                     stop=stop, step=step)
            except:  # It's probably a striplog.
                continue

        return

    def get_mnemonics_from_regex(self, pattern):
        """
        Should probably integrate getting curves with regex, vs getting with
        aliases, even though mixing them is probably confusing. For now I can't
        think of another use case for these wildcards, so I'll just implement
        for the curve table and we can worry about a nice solution later if we
        ever come back to it.
        """
        regex = re.compile(pattern)
        keys = list(self.data.keys())
        return [m.group(0) for k in keys for m in [regex.search(k)] if m]

    def get_alias(self, mnemonic, alias=None):
        """
        Get the alias key that this mnemonic belongs to.

        Returns: str.
        """
        if alias is None:
            return mnemonic
        for k, v in alias.items():
            if mnemonic in v:
                return k
        return None

    def get_mnemonic(self, mnemonic, alias=None):
        """
        Instead of picking curves by name directly from the data dict, you
        can pick them up with this method, which takes account of the alias
        dict you pass it. If you do not pass an alias dict, then you get the
        curve you asked for, if it exists, or None. NB Wells do not have alias
        dicts, but Projects do.

        Args:
            mnemonic (str): the name of the curve you want.
            alias (dict): an alias dictionary, mapping mnemonics to lists of
                mnemonics.

        Returns:
            str.
        """
        alias = alias or {}
        aliases = alias.get(mnemonic, [mnemonic])
        for a in aliases:
            if a in self.data:
                return a
        return None

    def get_curve(self, mnemonic, alias=None):
        """
        Wraps get_mnemonic.

        Instead of picking curves by name directly from the data dict, you
        can pick them up with this method, which takes account of the alias
        dict you pass it. If you do not pass an alias dict, then you get the
        curve you asked for, if it exists, or None. NB Wells do not have alias
        dicts, but Projects do.

        Args:
            mnemonic (str): the name of the curve you want.
            alias (dict): an alias dictionary, mapping mnemonics to lists of
                mnemonics.

        Returns:
            Curve.
        """
        return self.data.get(self.get_mnemonic(mnemonic, alias=alias), None)

    def count_curves(self, keys=None, alias=None):
        """
        Counts the number of curves in the well that will be selected with the
        given key list and the given alias dict. Used by Project's curve table.
        """
        keys = self._get_curve_mnemonics(keys, alias=alias)

        return len(list(
            filter(None, [self.get_mnemonic(k, alias=alias) for k in keys])))

    def is_complete(self, keys=None, alias=None):
        """
        Returns False if the well does not have one or more of the keys in its
        data dictionary. Used by ``project.data_to_matrix()``.
        """
        return any(k not in list(self.data.keys()) for k in keys)

    def alias_has_multiple(self, mnemonic, alias):
        return 1 < len([a for a in alias[mnemonic] if a in self.data])

    def make_synthetic(self, srd=0, v_repl_seismic=2000, v_repl_log=2000, f=50,
                       dt=0.001):
        """
        Early hack. Use with extreme caution.

        Hands-free. There'll be a more granualr version in synthetic.py.

        Assumes DT is in µs/m and RHOB is kg/m3.

        There is no handling yet for TVD.

        The datum handling is probably sketchy.
        """
        kb = getattr(self.location, 'kb', None) or 0
        data0 = self.data['DT'].start
        log_start_time = ((srd - kb) / v_repl_seismic) + (data0 / v_repl_log)

        # Basic log values.
        dt_log = self.data['DT'].despike()  # assume µs/m
        rho_log = self.data['RHOB'].despike()  # assume kg/m3
        if not np.allclose(dt_log.basis, rho_log.basis):
            rho_log = rho_log.to_basis_like(dt_log)
        Z = (1e6 / dt_log) * rho_log

        # Two-way-time.
        scaled_dt = dt_log.step * np.nan_to_num(dt_log) / 1e6
        twt = 2 * np.cumsum(scaled_dt)
        t = twt + log_start_time

        # Move to time.
        t_max = t[-1] + 10 * dt
        t_reg = np.arange(0, t_max + 1e-9, dt)
        Z_t = np.interp(x=t_reg, xp=t, fp=Z)

        # Make RC series.
        rc_t = (Z_t[1:] - Z_t[:-1]) / (Z_t[1:] + Z_t[:-1])
        rc_t = np.nan_to_num(rc_t)

        # Convolve.
        _, ricker = utils.ricker(f=f, length=0.128, dt=dt)
        synth = np.convolve(ricker, rc_t, mode='same')

        params = {'dt': dt, 'z start': dt_log.start, 'z stop': dt_log.stop}

        self.data['Synthetic'] = Synthetic(synth, basis=t_reg, params=params)

        return None

    def qc_curve_group(self, tests, keys=None, alias=None):
        """
        Run tests on a cohort of curves. Wrapping functions from quality.py

        Args:
            tests (dict): a dictionary of tests, mapping mnemonics to lists of
                tests. Two special keys, `all` and `each` map tests to the set
                of all curves, and to each curve in the well, respectively.
                You only need `all` if the test involves multiple inputs, e.g.
                comparing one curve to another.
            keys (list): a list of the mnemonics to run the tests against.
            alias (dict): an alias dictionary, mapping mnemonics to lists of
                mnemonics.

        Returns:
            dict.
        """
        return qc_curve_group_well(well=self, tests=tests, keys=keys,
                                   alias=alias)

    def qc_data(self, tests, keys=None, alias=None):
        """
        Run a series of tests against the data and return the corresponding
        results. Wrapping frunction from quality.py.

        Args:
            tests (dict): a dictionary of tests, mapping mnemonics to lists of
                tests. Two special keys, `all` and `each` map tests to the set
                of all curves, and to each curve in the well, respectively.
                You only need `all` if the test involves multiple inputs, e.g.
                comparing one curve to another.
            keys (list): a list of the mnemonics to run the tests against.
            alias (dict): an alias dictionary, mapping mnemonics to lists of
                mnemonics.

        Returns:
            list. The results. Stick to booleans (True = pass) or ints.
        """
        return qc_data_well(well=self, tests=tests, keys=keys, alias=alias)

    def qc_table_html(self, tests, keys=None, alias=None):
        """
        Makes a nice table out of ``qc_data()`` Wrapping function from quality.py.

        Returns:
            str. An HTML string.
        """
        return qc_table_html_well(well=self, tests=tests, keys=keys,
                                  alias=alias)

    def to_canstrat(self, key, log, lith_field, filename=None, as_text=False):
        """
        Make a Canstrat DAT (aka ASCII) file.

        TODO:
            The data part should probably belong to striplog, and only the
            header should be written by the well.

        Args:
           filename (str)
           key (str)
           log (str): the log name, should be 6 characters.
           lith_field (str) the name of the lithology field in the striplog's
               Primary component. Must match the Canstrat definitions.
           filename (str)
           as_text (bool): if you don't want to write a file.
        """
        if (filename is None):
            if (not as_text):
                m = "You must provide a filename or set as_text to True."
                raise WellError(m)

        strip = self.data[key]
        strip = strip.fill()  # Default is to fill with 'null' intervals.

        record = {1: [well_to_card_1(self)], 2: [well_to_card_2(self, key)],
                  8: [],
                  7: [interval_to_card_7(iv, lith_field) for iv in strip]}

        result = ''
        for c in [1, 2, 8, 7]:
            for d in record[c]:
                result += write_row(d, card=c, log=log)

        if as_text:
            return result
        else:
            with open(filename, 'w') as f:
                f.write(result)
            return None

    def data_as_matrix(self, keys=None, return_basis=False, basis=None,
                       alias=None, start=None, stop=None, step=None,
                       window_length=None, window_step=1, ):
        """
        Provide a feature matrix, given a list of data items.

        I think this will probably fail if there are striplogs in the data
        dictionary for this well.

        TODO:
            Deal with striplogs and other data, if present.

        Args:
            keys (list): List of the logs to export from the data dictionary.
            return_basis (bool): Whether or not to return the basis that was
                used.
            basis (ndarray): The basis to use. Default is to survey all curves
                to find a common basis.
            alias (dict): A mapping of alias names to lists of mnemonics.
            start (float): Optionally override the start of whatever basis
                you find or (more likely) is surveyed.
            stop (float): Optionally override the stop of whatever basis
                you find or (more likely) is surveyed.
            step (float): Override the step in the basis from survey_basis.
            window_length (int): The number of samples to return around each sample.
                This will provide one or more shifted versions of the features.
            window_step (int): How much to step the offset versions.

        Returns:
            ndarray.
            or
            ndarray, ndarray if return_basis=True
        """
        if keys is None:
            keys = [k for k, v in self.data.items() if isinstance(v, Curve)]
        else:
            # Only look at the alias list if keys were passed.
            if alias is not None:
                _keys = []
                for k in keys:
                    if k in alias:
                        added = False
                        for a in alias[k]:
                            if a in self.data:
                                _keys.append(a)
                                added = True
                                break
                        if not added:
                            _keys.append(k)
                    else:
                        _keys.append(k)
                keys = _keys

        if basis is None:
            basis = self.survey_basis(keys=keys, step=step)

        # Get the data, or None is curve is missing.
        data = [self.data.get(k) for k in keys]

        # Now cast to the correct basis, and replace any missing curves with
        # an empty Curve. The sklearn imputer will deal with it. We will change
        # the elements in place.
        for i, d in enumerate(data):
            if d is not None:
                data[i] = d.to_basis(basis=basis)
                # Allow user to override the start and stop from the survey.
                if (start is not None) or (stop is not None):
                    data[i] = data[i].to_basis(start, stop, step)
                    basis = data[i].basis
            else:
                # Empty_like gives unpredictable results
                data[i] = Curve(np.full(basis.shape, np.nan), basis=basis)

        if window_length is not None:
            d_new = []
            for d in data:
                r = d._rolling_window(window_length, func1d=utils.null,
                                      step=window_step, return_rolled=False, )
                d_new.append(r.T)
            data = d_new

        if return_basis:
            return np.vstack(data).T, basis
        else:
            return np.vstack(data).T

