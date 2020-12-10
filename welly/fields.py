"""
Field mapping from welly to LAS.

:copyright: 2021 Agile Geoscience
:license: Apache 2.0
"""
from .crs import CRS


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
        'northing': ('well', 'NS'),
        'easting': ('well', 'EW'),
        'x': ('well', 'XCOORD'),
        'y': ('well', 'YCOORD'),
        'datum': ('well', 'GDAT'),
        'section': ('well', 'SECT'),
        'range': ('well', 'RANG'),
        'township': ('well', 'TOWN'),
        'api': ('well', 'API'),
        'ekb': ('params', 'EKB'),
        'egl': ('params', 'EGL'),
        'kb': ('params', 'KB'),
        'gl': ('params', 'GL'),
        'td': ('params', 'TD'),
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
        'date': ('well', 'DATE')
    }
}


dev_fields = {
    'x': (r"X-COORDINATE: ([.0-9]+).+?", float),
    'y': (r"Y-COORDINATE: ([.0-9]+).+?", float),
    'kb': (r"# WELL DATUM .+?: ([.0-9]+).+?", float),
    'crs': (r"XYZ TRACE .+? \[\d+_(\d+)\] .+?", CRS.from_epsg),
}
