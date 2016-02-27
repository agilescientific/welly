#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Field mapping from welly to LAS.

:copyright: 2016 Agile Geoscience
:license: Apache 2.0
"""

las_fields = {
    'well': {
    },
    'header': {
        'name': ('well', 'WELL'),
        'field': ('well', 'FLD'),
        'license': ('well', 'LIC'),
        'uwi': ('well', 'UWI'),
    },
    'location': {
        'country': ('well', 'CTRY'),
        'latitude': ('well', 'LATI'),
        'longitude': ('well', 'LONG'),
        'datum': ('well', 'GDAT'),
        'section': ('well', 'SECT'),
        'range': ('well', 'RANG'),
        'township': ('well', 'TOWN'),
        'kb': ('params', 'EKB'),
        'td': ('params', 'TDD'),
        'tdd': ('params', 'TDD'),
        'tdl': ('params', 'TDL'),
    },
    'curve': {
        'start': ('well', 'STRT'),
        'step': ('well', 'STEP'),
        'null': ('well', 'NULL'),
        'run': ('params', 'RUN'),
    }
}
