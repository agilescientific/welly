#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines well location.

:copyright: 2016 Agile Geoscience
:license: Apache 2.0
"""


class Location(object):
    def __init__(self, params):
        """
        Generic initializer for now.
        In ``mode`` 'w', data overwrites the existing contents
        """
        for k, v in params.items():
            if k and v:
                setattr(self, k, v)

        self.crs = {}

    @classmethod
    def from_lasio_well(cls, well):
        """
        Assumes we're starting with a lasio well object.
        """
        params = {}
        # arams['country'] = well['CTRY'].value
        # params['lat'] = well['LATI'].value
        # params['lon'] = well['LONG'].value
        # params['datum'] = well['GDAT'].value
        # params['section'] = well['SECT'].value
        # params['range'] = well['RANG'].value
        # params['township'] = well['TOWN'].value
        return cls(params)

    def set_crs(self, crs):
        self.crs = crs
