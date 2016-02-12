#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines well headers.

:copyright: 2016 Agile Geoscience
:license: Apache 2.0
"""
import csv


class Header(object):
    """
    The well header.

    Not the same as an LAS header, but we might get info from there.
    """
    def __init__(self, params):
        for k, v in params.items():
            if k and v:
                setattr(self, k, v)

    def __repr__(self):
        return self.__dict__.__repr__()

    @classmethod
    def from_las(cls, las_file):
        params = {}
        # Do stuff
        return cls(params)

    @classmethod
    def from_lasio_well(cls, well):
        print('Header.from_lasio_well')
        params = {}
        params['name'] = well['WELL'].value
        params['field'] = well['FLD'].value
        params['license'] = well['LIC'].value
        return cls(params)

    @classmethod
    def from_csv(cls, csv_file):
        try:
            param_dict = csv.DictReader(csv_file)
            return cls(param_dict)
        except:
            raise NotImplementedError
