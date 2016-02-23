#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines well headers.

:copyright: 2016 Agile Geoscience
:license: Apache 2.0
"""
import csv

from . import utils


class Header(object):
    """
    The well header.

    Not the same as an LAS header, but we might get info from there.
    """
    def __init__(self, params):
        """
        Generic initializer for now.
        """
        for k, v in params.items():
            if k and v:
                setattr(self, k, v)

    def __repr__(self):
        return self.__dict__.__repr__()

    @classmethod
    def from_lasio_well(cls, well):
        """
        Assumes we're starting with a lasio well object.
        """
        params = {}
        params['name'] = utils.lasio_get(well, 'WELL', 'value')
        params['field'] = utils.lasio_get(well, 'FLD', 'value')
        params['license'] = utils.lasio_get(well, 'LIC', 'value')
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
