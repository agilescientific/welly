"""
Field mapping from welly to LAS.

:copyright: 2021 Agile Geoscience
:license: Apache 2.0
"""
from .crs import CRS
from .utils import lasio_get

las_sections = {'well', 'params'}
las_fields = {
    'well': {
    },
    'header': {
        'name': [{'section': 'well', "code": 'WELL'}],
        'field': [{'section': 'well', "code": 'FLD'}],
        'license': [{'section': 'well', "code": 'LIC'}],
        'uwi': [{'section': 'well', "code": 'UWI'}],
        'api': [{'section': 'well', "code": 'API'}],
        'company': [{'section': 'well', "code": 'COMP'}],
    },
    'location': {
        'location': [{'section': 'well', "code": 'LOC'}],
        'country': [{'section': 'well', "code": 'CTRY'}],
        'province': [{'section': 'well', "code": 'PROV'}],
        'state': [{'section': 'well', "code": 'STAT'}],
        'county': [{'section': 'well', "code": 'CNTY'}],
        'latitude': [{'section': 'well', "code": 'LATI'}],
        'longitude': [{'section': 'well', "code": 'LONG'}],
        'northing': [{'section': 'well', "code": 'NS'},
                     {'section': 'well', "code": 'Y'}],
        'easting': [{'section': 'well', "code": 'EW'},
                    {'section': 'well', "code": 'X'}],
        'x': [{'section': 'well', "code": 'XCOORD'}],
        'y': [{'section': 'well', "code": 'YCOORD'}],
        'datum': [{'section': 'well', "code": 'GDAT'}],
        'section': [{'section': 'well', "code": 'SECT'}],
        'range': [{'section': 'well', "code": 'RANG'}],
        'township': [{'section': 'well', "code": 'TOWN'}],
        'api': [{'section': 'well', "code": 'API'}],
        'kb': [{'section': 'params', "code": 'KB'},
               {'section': 'params', "code": 'EKB'},
               {'section': 'params', "code": 'EREF', "secondary_code": 'DREF', "secondary_desc": ["KB", "K.B.", "KELLY BUSHING"]}],
        'gl': [{'section': 'params', "code": 'GL'},
               {'section': 'params', "code": 'EGL'},
               {'section': 'params', "code": 'EPD', "secondary_code": "PD", "secondary_desc": ["Ground Level", "G.L.", "GROUND LEVEL"]},
               {'section': 'params', "code": 'Elevation', "secondary_code": "PermDatum", "secondary_desc": ["Ground Level", "G.L.", "GROUND LEVEL"]}],
        'td': [{'section': 'params', "code": 'TD'}],
        'tdd': [{'section': 'params', "code": 'TDD'}],
        'tdl': [{'section': 'params', "code": 'TDL'}],
    },
    'data': {
        'start': [{'section': 'well', "code": 'STRT'}],
        'stop': [{'section': 'well', "code": 'STOP'}],
        'step': [{'section': 'well', "code": 'STEP'}],
        'null': [{'section': 'well', "code": 'NULL'}],
        'run': [{'section': 'params', "code": 'RUN'}],
        'service_company': [{'section': 'well', "code": 'SRVC'}],
        'date': [{'section': 'well', "code": 'DATE'}],
    }
}


dev_fields = {
    'x': (r"X-COORDINATE: ([.0-9]+).+?", float),
    'y': (r"Y-COORDINATE: ([.0-9]+).+?", float),
    'kb': (r"# WELL DATUM .+?: ([.0-9]+).+?", float),
    'crs': (r"XYZ TRACE .+? \[\d+_(\d+)\] .+?", CRS.from_epsg),
}

def parse_fields(l, remap=None, funcs=None, initial_params=None,
                 field_alias=None, hdr_sect='header'):
    params = {}
    # print("parse_fields:", hdr_sect)
    if initial_params is not None:
        params = initial_params
    fields = field_alias
    if fields is None:
        fields = las_fields[hdr_sect]
    # print("____", fields)
    for field, values in fields.items():
        for val in values:
            params[field] = lasio_get(l,
                                      val,
                                    #   val['section'],
                                    #   val['code'],
                                    #   check=check,
                                      remap=remap,
                                      funcs=funcs)
            # print("_______", val, field, params[field])
            if params[field] is not None:
                break

    return params
