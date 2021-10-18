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

header_sections = [
    # LAS Versions: 1.2, 2, 3
    'Well',
    'W',
    'Version',
    'V',
    # LAS Versions: 1.2, 2
    'Curves',
    'C',
    'Parameter',
    'P',
    # LAS Versions: 3
    'Drilling_Parameter',
    'Drilling_Definition',
    'Core_Parameter',
    'Core_Definition',
    'Core_Parameter[1]',
    'Core_Definition[1]',
    'Core_Parameter[2]',
    'Core_Definition[2]',
    'Inclinometry_Parameter',
    'Inclinometry_Definition',
    'Log_Parameter',
    'Log_Definition',
    'Test_Parameter',
    'Test_Definition',
    'Tops_Parameter',
    'Tops_Definition',
    'TOPS_Definition',
    'Perforation_Parameter',
    'Perforation_Definition',
    'Perforations_Definition',
]

curve_sections = [
    # LAS Versions: 1.2, 2
    'Ascii',
    'ASCII',
    'A',
    'Curves',
    'C',
    # LAS Versions: 3
    'Drilling_Data',
    'Core_Data[1]',
    'Core_Data[2]',
    'Inclinometry_Data',
    'Test_Data',
    'Tops_Data',
    'Perforation_Data'
]

other_sections = [
    # LAS Versions: 1.2, 2
    'Other',  # Str
    'O'
]

las_objects = {
    'Version': 'version',
    'Well': 'well',
    'Curves': 'curves',
    'Parameter': 'params',
    'Other': 'other',
    'version': 'Version',
    'well': 'Well',
    'curves': 'Curves',
    'params': 'Parameter',
    'other': 'Other'
}
