"""
Defines a multi-well 'project'.

:copyright: 2021 Agile Scientific
:license: Apache 2.0
"""
from __future__ import print_function

import glob
from collections import Counter
from urllib.parse import non_hierarchical
import warnings

import numpy as np
import pandas as pd
from tqdm import tqdm

from .well import Well, WellError
from . import utils
from .utils import deprecated
from .plot import plot_kdes_project, plot_map_project


class Project(object):
    """
    Just a list of Well objects.

    One day it might want its own CRS, but then we'd have to cast the CRSs of
    the contained data.
    """

    def __init__(self, list_of_Wells, source=''):
        self.alias = {}
        self.source = source
        self.__list = list_of_Wells
        self.__index = 0

    def __repr__(self):
        s = [str(w.uwi) for w in self.__list]
        return "Project({} wells: {})".format(len(self), ', '.join(s))

    def __str__(self):
        s = [str(w.uwi) for w in self.__list]
        return '\n'.join(s)

    def __getitem__(self, key):
        if isinstance(key, slice):
            i = key.indices(len(self.__list))
            result = [self.__list[n] for n in range(*i)]
            return Project(result)
        elif isinstance(key, list):
            result = []
            for j in key:
                result.append(self.__list[j])
            return Project(result)
        else:
            return self.__list[key]

    def __setitem__(self, key, value):
        self.__list[key] = value

    def __delitem__(self, key):
        del(self.__list[key])

    def __iter__(self):
        for w in self.__list:
            yield w

    def __len__(self):
        return len(list(self.__list))

    def __contains__(self, item):
        if isinstance(item, Well):
            for d in self.__list:
                if item == d:
                    return True
        return False

    def __add__(self, other):
        if isinstance(other, self.__class__):
            result = self.__list + other.__list
            return Project(result)
        elif isinstance(other, Well):
            result = self.__list + [other]
            return Project(result)
        else:
            raise WellError("You can only add legends or decors.")

    def _repr_html_(self):
        """
        Jupyter Notebook magic repr function.
        """
        # Make header.
        r = '</th><th>'.join(['Index', 'UWI', 'Data', 'Curves'])
        rows = '<tr><th>{}</th></tr>'.format(r)

        # Make rows.
        for i, w in enumerate(self.__list):
            rows += '<tr><td>{}</td>'.format(i)
            rows += '<td><strong>{}</strong></td>'.format(w.uwi)
            rows += '<td>{}&nbsp;curves</td>'.format(len(w.data))
            rows += '<td>{}</td></tr>'.format(', '.join(w.data.keys()))
        html = '<table>{}</table>'.format(rows)

        return html

    def pop(self, index):
        item = self.__list.pop(index)
        self.__index = 0
        return item

    @property
    def uwis(self):
        """Returns the UWIs of the wells in the project."""
        return [w.uwi for w in self.__list]

    @property
    def basis_range(self):
        """
        Returns a tuple of the min and max of all the curves in the wells in the
        project.
        """
        idx = self.df().index.get_level_values('DEPT')
        return idx.min(), idx.max()

    @classmethod
    def from_las(cls,
                 path=None,
                 remap=None,
                 funcs=None,
                 data=True,
                 req=None,
                 alias=None,
                 max=None,
                 encoding=None,
                 printfname=None,
                 index=None,
                 **kwargs,
                 ):
        """
        Constructor. Essentially just wraps ``Well.from_las()``, but is more
        convenient for most purposes.

        Args:
            path (str or list): The path of the LAS files, e.g. ``./*.las`` (the
                default). It will attempt to load everything it finds, so
                make sure it only leads to LAS files.
            remap (dict): Optional. A dict of 'old': 'new' LAS field names.
            funcs (dict): Optional. A dict of 'las field': function() for
                implementing a transform before loading. Can be a lambda.
            data (bool): Whether to load curves or not.
            req (list): A list of alias names, giving all required curves. If
                not all of the aliases are present, the well is not loaded.
            alias (dict): The alias dict, e.g. ``alias = {'gamma': ['GR', 'GR1'], 'density': ['RHOZ', 'RHOB'], 'pants': ['PANTS']}``
            max (int): The max number of wells to load.
            encoding (str): File encoding; passed to lasio.
            printfname (bool): prints filename before trying to load it, for
                debugging
            index (str): Optional. Either "existing" (use the index as found in
                the LAS file) or "m", "ft" to use lasio's conversion of the
                relevant index unit.

        Returns:
            project. The project object.
        """
        if max is None:
            max = 1e12
        if (req is not None) and (alias is None):
            raise WellError("You need to provide an alias dict as well as requirement list.")

        if path is None:
            uris = glob.glob('./*.[LlAaSs]')
        elif isinstance(path, str):
            uris = glob.glob(path)
            if not uris:
                # The glob produced nothing.
                # URLs to 'folders' (eg a bucket) are not supported.
                # If it's a non-existent file, we'll get an error later.
                uris = [path]
        else:
            uris = path  # It's a list-like of files and/or URLs.

        wells = [Well.from_las(f,
                               remap=remap,
                               funcs=funcs,
                               data=data,
                               req=req,
                               alias=alias,
                               encoding=encoding,
                               printfname=printfname,
                               index=index,
                               **kwargs,
                               )
                 for i, f in tqdm(enumerate(uris)) if i < max]

        return cls(list(filter(None, wells)))

    def add_canstrat_striplogs(self, path, uwi_transform=None, name='canstrat'):
        """
        This may be too specific a method... just move it to the workflow.

        Requires striplog.
        """
        from striplog import Striplog

        uwi_transform = uwi_transform or utils.null

        for w in self.__list:
            try:
                dat_file = utils.find_file(str(uwi_transform(w.uwi)), path)
            except:
                print("- Skipping {}: something went wrong".format(w.uwi))
                continue

            if dat_file is None:
                print("- Omitting {}: no data".format(w.uwi))
                continue

            # If we got here, we're using it.
            print("+ Adding {} from {}".format(w.uwi, dat_file))

            w.data[name] = Striplog.from_canstrat(dat_file)

        return

    def __all_curve_names(self, uwis=None, unique=True, count=False, nodepth=True):
        """
        Utility function to get all curve names from all wells, regardless
        of data type or repetition.
        """
        uwis = uwis or self.uwis
        c = utils.flatten_list([list(w.data.keys()) for w in self if w.uwi in uwis])
        if nodepth:
            c = filter(lambda x: x not in ['DEPT', 'DEPTH'], c)
        if unique:
            if count:
                return Counter(c).most_common()
            else:
                return [i[0] for i in Counter(c).most_common()]
        return list(c)

    def get_mnemonics(self, mnemonics, uwis=None, alias=None):
        """
        Looks at all the wells in turn and returns the highest thing
        in the alias table.

        Args:
            mnemonics (list)
            alias (dict)

        Returns:
            list. A list of lists.
        """
        # Let's not do the nested comprehension...
        uwis = uwis or self.uwis
        wells = [w for w in self.__list if w.uwi in uwis]
        all_wells = []
        for w in wells:
            this_well = [w.get_mnemonic(m, alias=alias) for m in mnemonics]
            all_wells.append(this_well)
        return all_wells

    def count_mnemonic(self, mnemonic, uwis=uwis, alias=None):
        """
        Counts the wells that have a given curve, given the mnemonic and an
        alias dict.
        """
        all_mnemonics = self.get_mnemonics([mnemonic], uwis=uwis, alias=alias)
        return len(list(filter(None, utils.flatten_list(all_mnemonics))))

    def curve_table_html(self,
                         uwis=None,
                         keys=None,
                         alias=None,
                         tests=None,
                         exclude=None,
                         limit=0):
        """
        Another version of the curve table.

        Args:
            uwis (list): Only these UWIs. List of ``str``.
            keys (list): Only these names. List of ``str``.
            alias (dict): Alias table, maps names to mnemomnics in order of
                preference.
            tests (dict): Test table, maps names to lists of functions.
            exclude (list): Except these names. List of ``str``. Ignored if
                you pass ``keys``.
            limit (int): Curve must be present in at least this many wells.

        Returns:
            str. HTML representation of the table.
        """
        uwis = uwis or self.uwis
        wells = [w for w in self.__list if w.uwi in uwis]

        # This is hacky. See remark in well.get_mnemonics_from_regex().
        if exclude is not None:
            exclude = utils.flatten_list([w.get_mnemonics_from_regex(e) for e in exclude for w in wells])
            if alias is not None:
                exclude = [alias.get(e, e) for e in exclude]
        else:
            exclude = []

        counter = self.__all_curve_names(uwis=uwis, count=True)
        all_keys = [i[0] for i in counter
                    if (i[0] not in exclude) and (i[1] >= limit)]
        keys = utils.flatten_list(keys) or all_keys

        tests = tests or {}
        alias = alias or self.alias

        # Make header.
        keys_ = [k + '*' if k in alias else k for k in keys]
        r = '</th><th>'.join(['Idx', 'UWI', 'Data', 'Passing'] + keys_)
        rows = '<tr><th>{}</th></tr>'.format(r)

        # Make summary row.
        well_counts = [self.count_mnemonic(m, uwis=uwis, alias=alias)
                       for m in keys]
        w = len(wells)
        well_count_strs = ['{}/{}&nbsp;wells'.format(c, w) for c in well_counts]
        r = '</td><td>'.join(['', '', '', '%'] + well_count_strs)
        rows += '<tr><td>{}</td></tr>'.format(r)

        q_colours = {
            0: '#FF3333',
            1: '#33EE33',
            -1: '#AACCAA'
            # default: '#FFFFCC'  # Done with get when we use this dict.
        }

        # Make rows.
        for i, w in enumerate(wells):

            this_well = [w.get_curve(m, alias=alias)
                         for m in keys]

            q_well = w.qc_data(tests, keys=keys, alias=alias)

            curves = []
            q_total, q_count = 0, 0

            for c in this_well:
                q = -1
                num_tests, num_passes = 0, 0
                if c is None:
                    curves.append(('#CCCCCC', '', '', '#CCCCCC', '', ''))
                else:
                    if tests:
                        q_this = q_well.get(c.mnemonic)
                        if q_this:
                            results = q_this.values()
                            if results:
                                num_tests = len(results)
                                num_passes = sum(results)
                                q = num_passes / num_tests
                    q_colour = q_colours.get(q, '#FFCC33')
                    c_mean = '{:.2f}'.format(float(np.nanmean(c.df.values))) if np.any(c.df.values[~np.isnan(c.df.values)]) else np.nan
                    curves.append(('#CCEECC', c.mnemonic, f"{num_passes}/{num_tests}", q_colour, c_mean, c.units))
                q_total += num_passes
                q_count += num_tests

            # Make general columns.
            count = w.count_curves(keys, alias)
            if count == 0:
                score = '–'
            else:
                score = '{:.0f}'.format(100 * (q_total / q_count)) if (q_total >= 0) and (q_count > 0) else '–'
            s = '<tr><td>{}</td><td><span style="font-weight:bold;">{}</span></td><td>{}/{}&nbsp;curves</td><td>{}</td>'
            rows += s.format(i, w.uwi, count, len(w.data), score)

            # Make curve data columns.
            for curve in curves:
                s = '<td style="background-color:{}; line-height:80%; padding:5px 4px 2px 4px;">{}'
                t = '<div title="{{}}" style="font-size:80%; float:right; cursor: default; padding:4px 0px 4px 6px; color:{{}};">{0}</div>'
                if tests:
                    t = t.format('&#x2b24;')
                else:
                    t = t.format('')
                s += t
                s += '<br /><span style="font-size:70%; color:#33AA33">{} {}</span></td>'
                rows += s.format(*curve)
            rows += '</tr>'

        # Make the table and get out of here.
        html = '<table>{}</table>'.format(rows)
        return html

    def plot_map(self, fields=('x', 'y'), ax=None, label=None, width=6):
        """
        Plot a map of the wells in the project.

        Args:
            fields (list): The two fields of the `location` object to use
                as the x and y coordinates. Default: `('x', 'y')`
            ax (matplotlib.axes.Axes): An axes object to plot into. Will be
                returned. If you don't pass one, we'll create one and give
                back the `fig` that it's in.
            label (str): The field of the `Well.header` object to use as the label.
                Default: `Well.header.name`.
            width (float): The width, in inches, of the plot. Default: 6 in.

        Returns:
            matplotlib.figure.Figure, or matplotlib.axes.Axes if you passed in
                an axes object as `ax`.
        """
        return plot_map_project(project=self,
                                fields=fields,
                                ax=ax,
                                label=label,
                                width=width)

    def plot_kdes(self, mnemonic, alias=None, uwi_regex=None):
        """
        Plot KDEs for all curves with the given name.

        Args:
            mnemonic (str): the name of the curve to look for.
            alias (dict): a welly alias dictionary.
                e.g. {'density': ['DEN', 'DENS']}
            uwi_regex (str): a regex pattern. Only this part of the UWI will be displayed
                on the plot of KDEs.

        Returns:
            None or figure.
        """
        return plot_kdes_project(project=self,
                                 mnemonic=mnemonic,
                                 alias=alias,
                                 uwi_regex=uwi_regex,
                                )

    @deprecated('Project.find_wells_with_curve() is deprecated; use Project.filter_wells_by_data().')
    def find_wells_with_curve(self, mnemonic, alias=None):
        """
        Returns a new Project with only the wells which have the named curve.

        Args:
            mnemonic (str): the name of the curve to look for.
            alias (dict): a welly alias dictionary.
                e.g. {'density': ['DEN', 'DENS']}
        
        Returns:
            project.
        """
        return self.filter_wells_by_data([mnemonic], alias=alias)

    @deprecated('Project.find_wells_without_curve() is deprecated; use Project.filter_wells_by_data().')
    def find_wells_without_curve(self, mnemonic, alias=None):
        """
        Returns a new Project with only the wells which DO NOT have the named curve.

        Args:
            menmonic (str): the name of the curve to look for.
            alias (dict): a welly alias dictionary.
                e.g. {'density': ['DEN', 'DENS']}
        
        Returns:
            project.
        """
        return self.filter_wells_by_data([mnemonic], func='nany', alias=alias)

    def filter_wells_by_data(self, keys, alias=None, func='all'):
        """
        Returns a new Project with only the wells which have the named data.

        Args:
            keys (list): the names of the data or curves to look for.
            alias (dict): a welly alias dictionary.
                e.g. {'density': ['DEN', 'DENS']}
            func (str or function): a string from ['any', 'all', 'nany', 'nall']
                or a runnable function returning a boolean. Return True for
                wells you want to select. 'any' means you want wells which have
                any of the data keys specified in `keys`; 'all' means you need
                the well to have all of the keys. Conversely, 'nany' means you
                need the well to not have any of the named keys; 'nall' means
                you need the well to not have all of them (so a well with 4 of
                5 named keys would be selected).
        
        Returns:
            project.
        """
        if isinstance(keys, str):
            with warnings.catch_warnings():
                warnings.simplefilter("always")
                w = "The `keys` argument should be an iterable of keys in a "
                w += "well's `data` dictionary. Try passing a list of strings."
                warnings.warn(w, stacklevel=2)

        funcs = {
            'any': any,
            'all': all,
            'nany': lambda x: not any(x),
            'nall': lambda x: not all(x),
        }
        f = funcs.get(func, func)

        return Project([w for w in self if f(w.get_mnemonic(k, alias=alias) for k in keys)])

    def get_wells(self, uwis=None):
        """
        Returns a new Project with only the wells named by UWI.

        Args:
            uwis (list): list or tuple of UWI strings.
        
        Returns:
            project.
        """
        if uwis is None:
            return Project(self.__list)
        return Project([w for w in self if w.uwi in uwis])

    def omit_wells(self, uwis=None):
        """
        Returns a new project where wells with specified uwis have been omitted

        Args: 
            uwis (list): list or tuple of UWI strings.

        Returns: 
            project
        """
        if uwis is None:
            raise ValueError('Must specify at least one uwi')
        return Project([w for w in self if w.uwi not in uwis])

    def get_well(self, uwi):
        """
        Returns a Well object identified by UWI

        Args:
            uwi (string): the UWI string for the well.
        
        Returns:
            well
        """
        matching_wells = [w for w in self if w.uwi == uwi]
        return matching_wells[0] if len(matching_wells) >= 1 else None

    def merge_wells(self, right, keys=None):
        """
        Returns a new Project object containing wells from self where
        curves from the wells on the right have been added. Matching between
        wells in self and right is based on uwi match and ony wells in self
        are considered.

        Args:
            right (Project): Project with well that needs to be merged.
            keys (list): list of mnemonics to merge.
        
        Returns:
            Project
        """
        wells = []
        for w in self:
            rw = right.get_well(w.uwi)
            if rw is not None:
                if keys is None:
                    keys = list(rw.data.keys())
                for k in keys:
                    try:
                        w.data[k] = rw.data[k]
                    except:
                        pass
            wells.append(w)
        return Project(wells)

    def df(self, keys=None, basis=None, alias=None, rename_aliased=True):
        """
        Makes a pandas DataFrame containing Curve data for all the wells
        in the Project. The DataFrame has a dual index of well UWI and
        curve Depths. Requires `pandas`.

        Args:
            keys (list): List of strings: the keys of the data items to
                survey, if not all of them.
            basis (array): A basis, if you want to enforce one, otherwise
                you'll get the result of ``survey_basis()``.
            alias (dict): Alias dictionary.
                e.g. {'density': ['DEN', 'DENS']}
            rename_aliased (bool): Whether to name the columns after the alias,
                i.e. the alias dictionary key, or after the curve mnemonic.
                Default is False, do not rename: use the mnemonic.

        Returns:
            ``pandas.DataFrame``.
        """
        dfs = []
        for w in self:
            try:
                df = w.df(uwi=True, keys=keys, basis=basis, alias=alias, rename_aliased=rename_aliased)
            except WellError:
                # Probably there's no data for this well.
                df = None
            dfs.append(df)

        return pd.concat(dfs)

    def data_as_matrix(self,
                       X_keys,
                       y_key=None,
                       alias=None,
                       legend=None,
                       match_only=None,
                       field=None,
                       field_function=None,
                       table=None,
                       legend_field=None,
                       basis=None,
                       step=None,
                       window_length=None,
                       window_step=1,
                       test=None,
                       remove_zeros=False,
                       include_basis=False,
                       include_index=False,
                       include=None):
        """
        Create train matrices of wells in project for mnemonic keys. Optionally add test
        matrices.

        Args:
            X_keys (list): list mnemonics to create `X_train` matrices from
            y_key (str): mnemonic to create `y_train` matrix
            alias (dict): a dictionary mapping mnemonics to lists of mnemonics.
                e.g. {'density': ['DEN', 'DENS']}
            legend (Legend): Passed to `striplog.to_log()`. If you want the codes to come
                from a legend, provide one. Otherwise the codes come from the log, using
                integers in the order of prevalence. If you use a legend,
                they are assigned in the order of the legend.
            match_only (list): Passed to `striplog.to_log()`. If you only want to match
                some attributes of the Components (e.g. lithology), provide a list of
                those you want to match.
            field (str): Passed to `striplog.to_log()`. If you want the data to come from
                one of the attributes of the components in the striplog, provide it.
            field_function (function): Passed to `striplog.to_log()`. Provide a function
                to apply to the field you are asking for. It's up to you to make sure the
                function does what you want.
            table (list): Passed to `striplog.to_log()`. Provide a look-up table of values
                if you want. If you don't, then it will be constructed from the data.
            legend_field (str): Passed to `striplog.to_log()`. If you want to get a log
                representing one of the fields in the legend, such as 'width' or
                'grainsize'.
            basis (np.array or list): basis to be used for returned sliced data
            step (float or int): step used for reindexing curve basis
            window_length (int): The number of samples to return around each sample.
                This will provide one or more shifted versions of the features.
            window_step (int): How much to step the offset versions.
            test (list): UWIs to create test matrices from.
            remove_zeros (bool): Whether to remove zeros from matrices
            include_basis (bool): Whether to include basis in matrices
            include_index (bool): Whether to include index in matrices
            include (np.array): An additional array to include in the matrices.

        Returns:
            X_train, X_test, y_train, y_test (np.arrays): train and test matrices.
        """
        test = test or []

        train_, test_ = [], []

        for w in self.__list:
            if w.uwi in test:
                test_.append(w.uwi)
            else:
                train_.append(w.uwi)

        # create matrices for train wells
        X_train, y_train = self._data_as_matrix(X_keys=X_keys,
                                                y_key=y_key,
                                                alias=alias,
                                                legend=legend,
                                                match_only=match_only,
                                                field=field,
                                                field_function=field_function,
                                                table=table,
                                                legend_field=legend_field,
                                                basis=basis,
                                                step=step,
                                                window_length=window_length,
                                                window_step=window_step,
                                                uwis=train_,
                                                include_basis=include_basis,
                                                include_index=include_index,
                                                include=include)

        if y_train is None:
            return

        if remove_zeros:
            X_train = X_train[np.nonzero(y_train)]
            y_train = y_train[np.nonzero(y_train)]

        if not test:
            return X_train, y_train

        # create matrices for test wells
        X_test, y_test = self._data_as_matrix(X_keys=X_keys,
                                              y_key=y_key,
                                              alias=alias,
                                              legend=legend,
                                              match_only=match_only,
                                              field=field,
                                              field_function=field_function,
                                              table=table,
                                              legend_field=legend_field,
                                              basis=basis,
                                              step=step,
                                              window_length=window_length,
                                              window_step=window_step,
                                              uwis=test_,
                                              include_basis=include_basis,
                                              include_index=include_index,
                                              include=include)

        if remove_zeros:
            X_test = X_test[np.nonzero(y_test)]
            y_test = y_test[np.nonzero(y_test)]

        return X_train, X_test, y_train, y_test

    def _data_as_matrix(self,
                        X_keys,
                        y_key=None,
                        alias=None,
                        legend=None,
                        match_only=None,
                        field=None,
                        field_function=None,
                        legend_field=None,
                        table=None,
                        basis=None,
                        step=None,
                        window_length=None,
                        window_step=1,
                        uwis=None,
                        include_basis=False,
                        include_index=False,
                        include=None):
        """
        Make X and y matrices
        """
        alias = alias or self.alias
        if include is not None:
            include = np.array(include)

        if window_length is None:
            window_length = 1

        # Seed with known size.
        cols = window_length * len(X_keys)
        cols += sum([include_basis, include_index])

        def get_cols(q):
            if q is None: return 0
            a = np.array(q)
            try:
                s = a.shape[0]
            except IndexError:
                s = 1
            return s

        cols += get_cols(include)

        X = np.zeros(cols)
        y = np.zeros(1)

        # Build up the data.
        for i, w in enumerate(self.get_wells(uwis)):

            print(w.uwi, end=' ')

            if not w.is_complete(X_keys, alias):
                continue

            _X, z = w.data_as_matrix(X_keys,
                                     basis=basis,
                                     step=step,
                                     window_length=window_length,
                                     window_step=window_step,
                                     return_basis=True,
                                     alias=alias)
            if include is not None:
                try:
                    if np.ndim(include) == 0:
                        x = include * np.ones_like(z)
                        _X = np.hstack([np.expand_dims(x, 1), _X])
                    elif np.ndim(include) == 1:
                        for c in include:
                            x = c * np.ones_like(z)
                            _X = np.hstack([np.expand_dims(x, 1), _X])
                    elif np.ndim(include) == 2:
                        for c in include:
                            x = c[i] * np.ones_like(z)
                            _X = np.hstack([np.expand_dims(x, 1), _X])
                    else:
                        raise IndexError('Too many dimensions in include.')
                except:
                    raise WellError('Problem broadcasting include into X matrix.')

            if include_basis:
                _X = np.hstack([np.expand_dims(z, 1), _X])

            if include_index:
                index = i * np.ones_like(z)
                _X = np.hstack([np.expand_dims(index, 1), _X])

            X = np.vstack([X, _X])
            print(_X.shape[0])

            y_key_sel = w.get_mnemonic(y_key, alias=alias)

            if y_key_sel is None:
                continue

            try:
                # it's a `curve` object
                _y = w.data[y_key_sel].to_basis(basis=z)
            except:
                # it's probably a `striplog` object
                _y = w.data[y_key_sel].to_log(basis=z,
                                              legend=legend,
                                              match_only=match_only,
                                              field=field,
                                              field_function=field_function,
                                              table=table,
                                              legend_field=legend_field)
            if _y.shape[1] == 1:
                y = np.hstack([y, _y.df.to_numpy()[:, 0]])
            else:
                y = np.hstack([y, _y.df.to_numpy()])

        # Get rid of the 'seed'.
        X = X[1:]
        if y_key is None:
            y = None
        else:
            y = y[1:]

        return X, y
