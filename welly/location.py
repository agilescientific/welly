#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines well location.

:copyright: 2016 Agile Geoscience
:license: Apache 2.0
"""


class Location(object):
    def __init__(self, params):
        for k, v in params.items():
            if k and v:
                setattr(self, k, v)

    @classmethod
    def from_lasio_well(cls, well):
        print('Location.from_lasio_well')
        params = {}
        params['country'] = well['CTRY'].value
        params['lat'] = well['LATI'].value
        params['lon'] = well['LONG'].value
        params['datum'] = well['GDAT'].value
        params['section'] = well['SECT'].value
        params['range'] = well['RANG'].value
        params['township'] = well['TOWN'].value
        return cls(params)
