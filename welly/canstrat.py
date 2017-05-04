# -*- coding: utf 8 -*-
"""
Functions for importing Canstrat ASCII files.

:copyright: 2016 Agile Geoscience
:license: Apache 2.0
"""
import datetime as dt

from .utils import null, skip, are_close

from .canstrat_codes import rtc
from .canstrat_codes import fwork
from .canstrat_codes import grains
from .canstrat_codes import colour
from .canstrat_codes import cmod
from .canstrat_codes import porgrade
from .canstrat_codes import stain
from .canstrat_codes import oil


def _colour_read(x):
    try:
        c1 = colour[x[1]]
    except:
        c1 = ''
    try:
        c0 = colour[x[0]]
    except:
        c0 = ''
    try:
        m = cmod[x[2]]
    except:
        m = ''
    return ' '.join([m, c0, c1]).strip().replace('  ', ' ')


def _get_date(date_string):
    try:
        date = dt.datetime.strptime(date_string, "%y-%m-%d")
    except:
        date = dt.datetime.strptime("00-01-01", "%y-%m-%d")
    if dt.datetime.today() < date:
        date -= dt.timedelta(days=100*365.25)
    return dt.datetime.date(date)


def _put_date(date):
    if date:
        return dt.datetime.strftime(date, '%y-%m-%d')
    else:
        return '00-00-00'


columns_ = {
    # name: start, run, read, write
    'log':  [0,    6, null, null],
    'card': [6,    1, lambda x: int(x) if x else None, null],
    'skip': [7,    1, lambda x: True if x == 'X' else False, lambda x: 'X' if x else ' '],
    'core': [8,    1, lambda x: True if x == 'C' else False, lambda x: 'C' if x else ' '],
    'data': [9,    73,  null, null],
}


# Columns for card type 1
columns_1 = {
    'location': [8, 18, lambda x: x.strip(), null],
    'loctype': [18, 1, lambda x: {' ': 'NTS', '-': 'LL'}.get(x, 'LSD'), null],
    'units': [26, 1, null, null],
    'name': [27, 40, lambda x: x.strip(), null],
    'kb': [67, 2, null, null],
    'elev': [69, 5, lambda x: float(x)/10, lambda x: '{:5.0f}'.format(10*x)],
    'metric': [74, 1, lambda x: x if x == 'M' else 'I', lambda x: x if x == 'M' else ' '],
    'td': [75, 5, lambda x: float(x)/10, lambda x: '{:5.0f}'.format(10*x)],
}


# Columns for card type 1
columns_2 = {
    'spud': [8, 8, _get_date, _put_date],
    'comp': [18, 8, _get_date, _put_date],
    'status': [27, 13, lambda x: x.strip(), null],
    'uwi': [50, 16, null, null],
    'start': [69, 5, lambda x: float(x)/10, lambda x: '{:5.0f}'.format(10*x)],
    'stop': [75, 5, lambda x: float(x)/10, lambda x: '{:5.0f}'.format(10*x)],
}


# Columns for card type 1
columns_8 = {
    'formation': [14, 3, lambda x: x.strip(), null],
    'top': [24, 5, lambda x: float(x)/10, lambda x: '{:5.0f}'.format(10*x)],
}


columns_7 = {
    'skip': [7, 1, lambda x: True if x == 'X' else False, lambda x: 'X' if x else ' '],
    'core': [8, 1, lambda x: True if x == 'C' else False, lambda x: 'C' if x else ' '],
    'top': [9, 5, lambda x: float(x)/10, lambda x: '{:5.0f}'.format(10*x)],
    'base': [14, 5, lambda x: float(x)/10, lambda x: '{:5.0f}'.format(10*x)],
    'lithology': [19, 8, lambda x: x.replace(' ', '.'), skip],
    'rtc_id': [19, 1, null, lambda x: {v: k for k, v in rtc.items()}.get(x, '')],
    'rtc': [19, 1, lambda x: rtc[x], skip],
    'rtc_idperc': [20, 1, lambda x: int(x)*10 if int(x) > 0 else 100, lambda x: '{:1.0f}'.format(x/10) if x < 100 else '0'],
    'grains_mm': [21, 1, lambda x: grains[x], lambda x: [k for k, v in grains.items() if are_close(v, x)][0]],
    'framew_per': [22, 2, lambda x: fwork[x], lambda x: {v: k for k, v in fwork.items()}[x]],
    'colour': [24, 3, lambda x: x.replace(' ', '.'), lambda x: x.replace('.', ' ')],
    'colour_name': [24, 3, _colour_read, skip],
    'accessories': [27, 18, lambda x: x.strip(), lambda x: '{:18s}'.format(x)],
    'porgrade': [45, 1,  lambda x: porgrade[x] if x.replace(' ', '') else 0, skip],
    'stain': [49, 1,  lambda x: stain.get(x, ' '), lambda x: {v: k for k, v in stain.items()}.get(x, '')],
    'oil': [49, 1,  lambda x: oil.get(x, 0), skip],
}


columns = {
    0: columns_,   # Row header, applies to every row
    1: columns_1,  # Location, depth measure, well name, elev, td
    2: columns_2,  # Spud and completion data, status, UWI, Interval coded
    7: columns_7,  # Lithology
    8: columns_8,  # Formation tops
}


def well_to_card_1(well):
    dictionary = {}
    try:
        dictionary['elev'] = well.location.kb
    except:
        dictionary['elev'] = 0.0
    dictionary['kb'] = 'KB'
    dictionary['location'] = ''
    dictionary['loctype'] = ''
    dictionary['metric'] = 'M'
    dictionary['name'] = well.header.name
    dictionary['td'] = well.location.td or 0.0
    dictionary['units'] = 'M'
    return dictionary


def well_to_card_2(well, key):
    """
    Args:
        well (Well)
        key (str): The key of the predicted Striplog in `well.data`.

    Returns:
        dict.
    """
    dictionary = {}
    dictionary['comp'] = ''
    dictionary['spud'] = ''
    dictionary['start'] = well.data[key].start.z
    dictionary['stop'] = well.data[key].stop.z
    dictionary['status'] = ''
    dictionary['uwi'] = well.header.uwi
    return dictionary


def interval_to_card_7(iv, lith_field):
    dictionary = {}
    dictionary['top'] = getattr(getattr(iv, 'top'), 'z')
    dictionary['base'] = getattr(getattr(iv, 'base'), 'z')
    if not iv:
        # Then this interval is empty
        dictionary['skip'] = 'X'
        return dictionary
    dictionary['rtc_id'] = getattr(getattr(iv, 'primary'), lith_field)
    dictionary['rtc_idperc'] = 100
    dictionary['porgrade'] = 0
    return dictionary


def _put_field(coldict, key, value):
    # Get and transform the item
    if value is not None:
        result = coldict[key]['write'](value)
    else:
        result = ''

    if result is None:
        result = ''

    result = str(result)

    # Reset the stop, depending on what we got.
    strt = coldict[key]['start']
    stop = strt + len(result)

    return strt, stop, result


def cols(c):
    # Construct the column dictionary that maps each field to
    # its start, its length, and its read and write functions.
    coldict = {k: {'start': s,
                   'len': l,
                   'read': r,
                   'write': w} for k, (s, l, r, w) in columns[c].items()}
    return coldict


def write_row(dictionary, card, log):
    """
    Processes a single row from the file.
    """
    rowhdr = {'card': card, 'log': log}

    # Do this as a list of 1-char strings.
    # Can't use a string b/c strings are immutable.
    row = [' '] * 80

    # Make the row header.
    for e in ['log', 'card']:
        strt, stop, item = _put_field(cols(0), e, rowhdr[e])
        if item is not None:
            row[strt:stop] = list(item)

    # Now make the rest of the row.
    for field in cols(card):
        strt, stop, item = _put_field(cols(card), field, dictionary.get(field))
        if item is not None:
            row[strt:stop] = list(item)

    return ''.join(row) + '\n'
