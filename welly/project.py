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
        self.alias = None
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

    @property
    def uwis(self):
        return [w.uwi for w in self.__list]

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

    def _curve_table_html_(self, uwis=None, keys=None, alias=None):
        """
        Another version of the curve table.
        """
        uwis = uwis or self.uwis
        wells = [w for w in self.__list if w.uwi in uwis]
        counter = self.__all_curve_names(uwis=uwis, count=True)
        keys = utils.flatten_list(keys) or [i[0] for i in counter]
        alias = alias or self.alias

        # Get every curve name in the project, and count them all. Determines
        # the order of the table columns.

        # Make header.
        curve_names = [i[0] for i in counter if i[0] in keys]
        r = '</th><th>'.join(['UWI', 'Data'] + curve_names)
        rows = '<tr><th>{}</th></tr>'.format(r)

        # Make summary row.
        curve_counts = [str(i[1])+'&nbsp;wells' for i in counter if i[0] in keys]
        r = '</td><td>'.join(['', ''] + curve_counts)
        rows += '<tr><td>{}</td></tr>'.format(r)

        # Make rows.
        for w in wells:

            curves = []
            for c in curve_names:
                m = w.get_mnemonic(c, alias=alias)
                if c in w.data:
                    curves.append(('#CCEECC', m))
                elif m in w.data:
                    curves.append(('#FFFFCC', m))
                else:
                    curves.append(('#FFCCCC', ''))

            rows += '<td>{}</td><td>{}&nbsp;curves</td>'.format(w.uwi, len(w.data))
            for curve in curves:
                rows += '<td bgcolor={}>{}</td>'.format(*curve)
            rows += '</tr>'
        html = '<table>{}</table>'.format(rows)

        return html

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

    def data_as_matrix(self, keys, window_length=3):
        """
        Make X.

        Needs to return z probably...

        """
        # Seed with known size.
        X = np.zeros(window_length * len(keys))

        # Build up the data.
        for w in self.__list:
            _X, _ = w.data_as_matrix(keys,
                                     window_length=window_length,
                                     return_basis=True,
                                     alias=self.alias)
            X = np.vstack([X, _X])

        # Get rid of the 'seed'.
        X = X[1:]

        return X

    def striplogs_as_vector(self, key, window_length=3):
        """
        Make y.

        All striplogs need to have the same name.

        """
        # Seed with known size.
        y = np.zeros(1)

        return y
