#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines a multi-well 'project'.

:copyright: 2016 Agile Geoscience
:license: Apache 2.0
"""
import glob
from collections import Counter

import numpy as np

from .well import Well, WellError
from . import utils
from .defaults import ALIAS  # For access by user.


class Project(object):
    """
    Just a list of Well objects.

    One day it might want its own CRS, but then we'd have to cast the CRSs of
    the contained data.

    """
    def __init__(self, list_of_Wells):
        self.alias = {}
        self.__list = list_of_Wells
        self.__index = 0
        self._iter = iter(self.__list)  # Set up iterable.

    def __repr__(self):
        s = [w.uwi for w in self.__list]
        return "Project({0})".format('\n'.join(s))

    def __str__(self):
        s = [w.uwi for w in self.__list]
        return '\n'.join(s)

    def __getitem__(self, key):
        if type(key) is slice:
            i = key.indices(len(self.__list))
            result = [self.__list[n] for n in range(*i)]
            return Project(result)
        elif type(key) is list:
            result = []
            for j in key:
                result.append(self.__list[j])
            return Project(result)
        else:
            return self.__list[key]

    def __setitem__(self, key, value):
        self.__list[key] = value

    def __iter__(self):
        return self

    def __next__(self):
        try:
            result = self.__list[self.__index]
        except IndexError:
            self.__index = 0
            raise StopIteration
        self.__index += 1
        return result

    def next(self):
        """
        Retains Python 2 compatibility.
        """
        return self.__next__()

    def __len__(self):
        return len(self.__list)

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
        r = '</th><th>'.join(['UWI', 'Data', 'Curves'])
        rows = '<tr><th>{}</th></tr>'.format(r)

        # Make rows.
        for w in self.__list:
            rows += '<tr><td>{}</td>'.format(w.uwi)
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
        return [w.uwi for w in self.__list]

    @classmethod
    def from_las(cls, path, remap=None, funcs=None):
        """
        Constructor. Essentially just wraps ``Well.from_las()``, but is more
        convenient for most purposes.

        Args:
            path (str): The path of the LAS files, e.g. 'data/*.las'. It will
                attempt to load everything it finds, so make sure it only leads
                to LAS files.
            remap (dict): Optional. A dict of 'old': 'new' LAS field names.
            funcs (dict): Optional. A dict of 'las field': function() for
                implementing a transform before loading. Can be a lambda.

        Returns:
            project. The project object.
        """
        list_of_Wells = [Well.from_las(f) for f in glob.iglob(path)]
        return cls(list_of_Wells)

    def add_canstrat_striplogs(self, path, name='canstrat'):
        """
        This may be to specific a method... just move it to the workflow.

        Requires striplog.
        """
        from striplog import Striplog

        for w in self.__list:
            dat_file = utils.find_file(w.uwi, path)

            if dat_file is None:
                print("- Omitting {}: no data".format(w.uwi))
                continue

            # If we got here, we're using it.
            print("+ Adding {}".format(w.uwi))

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

    def curve_table_html(self, uwis=None, keys=None, alias=None, tests=None):
        """
        Another version of the curve table.
        """
        uwis = uwis or self.uwis
        wells = [w for w in self.__list if w.uwi in uwis]
        counter = self.__all_curve_names(uwis=uwis, count=True)
        keys = utils.flatten_list(keys) or [i[0] for i in counter]

        tests = tests or {}
        if alias is None:
            alias = self.alias

        # Make header.
        r = '</th><th>'.join(['UWI', 'Data'] + keys)
        rows = '<tr><th>{}</th></tr>'.format(r)

        # Make summary row.
        well_counts = [str(self.count_mnemonic(m, uwis=uwis, alias=alias))+'&nbsp;wells' for m in keys]
        r = '</td><td>'.join(['', ''] + well_counts)
        rows += '<tr><td>{}</td></tr>'.format(r)

        q_colours = {
            0: '#FF3333',
            1: '#33FF33',
            -1: '#CCCCCC'
            # default: '#FFFFCC'  # Done with get when we use this dict.
        }

        # Make rows.
        for w in wells:

            this_well = [w.get_curve(m, alias=alias) for m in keys]

            curves = []
            for c in this_well:
                if c is None:
                    curves.append(('#CCCCCC', '', '#CCCCCC', ''))
                else:
                    q_colour = q_colours.get(c.quality_score(tests), '#FFCC33')
                    curves.append(('#CCEECC', c.mnemonic, q_colour, c.units))

            # Make general columns.
            s = '<td><span style="font-weight:bold;">{}</span></td><td>{}/{}&nbsp;curves</td>'
            rows += s.format(w.uwi, w.count_curves(keys, alias), len(w.data))

            # Make curve data columns.
            for curve in curves:
                s = '<td style="background-color:{}; line-height:80%; padding:5px 4px 2px 4px;">{}'
                t = '<div style="font-size:80%; float:right; padding:4px 0px 4px 6px; color:{{}};">{}</div>'
                if tests:
                    t = t.format('&#x2b24;')
                else:
                    t = t.format('')
                s += t
                s += '<br /><span style="font-size:70%; color:#33AA33">{}</span></td>'
                rows += s.format(*curve)
            rows += '</tr>'

        # Make the table and get out of here.
        html = '<table>{}</table>'.format(rows)
        return html

    def find_curves(self, curve):
        return [w for w in self if curve in w.data.keys()]

    def get_wells(self, uwis=None):
        if uwis is None:
            return Project(self.__list)
        return Project([w for w in self if w.uwi in uwis])

    def data_as_matrix(self, X_keys, y_key,
                       alias=None,
                       legend=None,
                       match_only=None,
                       basis=None,
                       window_length=3,
                       test=None,
                       remove_zeros=False):

        test = test or []
        train_, test_ = [], []
        for w in self.__list:
            if w.uwi in test:
                test_.append(w.uwi)
            else:
                train_.append(w.uwi)

        X_train, y_train = self._data_as_matrix(X_keys=X_keys, y_key=y_key,
                                                alias=alias,
                                                legend=legend,
                                                match_only=match_only,
                                                basis=basis,
                                                window_length=window_length,
                                                uwis=train_)

        if remove_zeros:
            X_train = X_train[np.nonzero(y_train)]
            y_train = y_train[np.nonzero(y_train)]

        if not test:
            return X_train, y_train

        X_test, y_test = self._data_as_matrix(X_keys=X_keys, y_key=y_key,
                                              alias=alias,
                                              legend=legend,
                                              match_only=match_only,
                                              basis=basis,
                                              window_length=window_length,
                                              uwis=test_)

        if remove_zeros:
            X_test = X_test[np.nonzero(y_test)]
            y_test = y_test[np.nonzero(y_test)]

        return X_train, X_test, y_train, y_test

    def _data_as_matrix(self, X_keys, y_key,
                        alias=None,
                        legend=None,
                        match_only=None,
                        basis=None,
                        window_length=3,
                        uwis=None):
        """
        Make X.

        """
        alias = alias or self.alias

        # Seed with known size.
        X = np.zeros(window_length * len(X_keys))
        y = np.zeros(1)

        # Build up the data.
        for w in self.get_wells(uwis):

            _X, z = w.data_as_matrix(X_keys,
                                     basis=basis,
                                     window_length=window_length,
                                     return_basis=True,
                                     alias=alias)
            X = np.vstack([X, _X])

            y_key = w.get_mnemonic(y_key, alias=alias)

            try:
                _y = w.data[y_key].to_basis(basis=z)
            except:
                _y = w.data[y_key].to_log(basis=z,
                                          legend=legend,
                                          match_only=match_only)

            y = np.hstack([y, _y])

        # Get rid of the 'seed'.
        X = X[1:]
        y = y[1:]

        return X, y
