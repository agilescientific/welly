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
        'api': ('well', 'API'),
        'company': ('well', 'COMP'),
    },
    'location': {
        'location': ('well', 'LOC'),
        'country': ('well', 'CTRY'),
        'province': ('well', 'PROV'),
        'state': ('well', 'STAT'),
        'county': ('well', 'CNTY'),
        'latitude': ('well', 'LATI'),
        'longitude': ('well', 'LONG'),
        'datum': ('well', 'GDAT'),
        'section': ('well', 'SECT'),
        'range': ('well', 'RANG'),
        'township': ('well', 'TOWN'),
        'api': ('well', 'API'),
        'kb': ('params', 'EKB'),
        'gl': ('params', 'EGL'),
        'td': ('params', 'TDD'),
        'tdd': ('params', 'TDD'),
        'tdl': ('params', 'TDL'),
    },
    'data': {
        'start': ('well', 'STRT'),
        'stop': ('well', 'STOP'),
        'step': ('well', 'STEP'),
        'null': ('well', 'NULL'),
        'run': ('params', 'RUN'),
        'service_company': ('well', 'SRVC'),
        'date': ('well', 'DATE'),
    }
}
