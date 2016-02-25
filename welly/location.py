#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines well location.

:copyright: 2016 Agile Geoscience
:license: Apache 2.0
"""
from . import utils
from .crs import CRS


class Location(object):
    def __init__(self, params):
        """
        Generic initializer for now.
        """
        self.crs = CRS(params.pop('crs', dict()))

        for k, v in params.items():
            if k and v:
                setattr(self, k, v)

    def __repr__(self):
        return 'Location({})'.format(self.__dict__)

    @classmethod
    def from_lasio_well(cls, well):
        """
        Assumes we're starting with a lasio well object.
        """
        params = {}
        params['country'] = utils.lasio_get(well, 'CTRY', 'value')
        params['lat'] = utils.lasio_get(well, 'LATI', 'value')
        params['lon'] = utils.lasio_get(well, 'LONG', 'value')
        params['datum'] = utils.lasio_get(well, 'GDAT', 'value')
        params['section'] = utils.lasio_get(well, 'SECT', 'value')
        params['range'] = utils.lasio_get(well, 'RANG', 'value')
        params['township'] = utils.lasio_get(well, 'TOWN', 'value')

        return cls(params)
