#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines well headers.

:copyright: 2016 Agile Geoscience
:license: Apache 2.0
"""
import csv

from .fields import las_fields
from . import utils


class Header(object):
    """
    The well metadata or header information.

    Not the same as an LAS header, but we might get info from there.
    """
    def __init__(self, params):
        """
        Generic initializer for now.
        """
        for k, v in params.items():
            if k and v:
                setattr(self, k, v)

        # if getattr(self, 'uwi', None) is None:
        #     self.uwi = ''

    def __repr__(self):
        return self.__dict__.__repr__()

    @classmethod
    def from_lasio(cls, l, remap=None, funcs=None):
        """
        Assumes we're starting with a lasio object, l.

        Args:
            l (lasio): A lasio instance.
            remap (dict): Optional. A dict of 'old': 'new' LAS field names.
            funcs (dict): Optional. A dict of 'las field': function() for
                implementing a transform before loading. Can be a lambda.

        """
        params = {}
        for field, (sect, code) in las_fields['header'].items():
            params[field] = utils.lasio_get(l,
                                            sect,
                                            code,
                                            remap=remap,
                                            funcs=funcs)
        return cls(params)

    @classmethod
    def from_csv(cls, csv_file):
        """
        Not implemented. Will provide a route from CSV file.
        """
        try:
            param_dict = csv.DictReader(csv_file)
            return cls(param_dict)
        except:
            raise NotImplementedError
