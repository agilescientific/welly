#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines intervals and rock for holding lithologies.

:copyright: 2015 Agile Geoscience
:license: Apache 2.0
"""
import time
import re
import warnings

from namedlist import namedlist

from . import las
from . import templates
from striplog import Striplog

# The standard library OrderedDict was introduced in Python 2.7 so
# we have a third-party option to support Python 2.6

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

HeaderItem = namedlist('HeaderItem', ['mnemonic', 'unit', 'value', 'descr'])


class OrderedDictionary(OrderedDict):

    '''A minor wrapper over OrderedDict.
    This wrapper has a better string representation.
    '''

    def __repr__(self):
        l = []
        for key, value in self.items():
            s = "'%s': %s" % (key, value)
            l.append(s)
        s = '{' + ',\n '.join(l) + '}'
        return s

DEFAULT_ITEMS = {
    'head': OrderedDictionary([
        ('UWI', HeaderItem('UWI', '', '', 'Unique Well ID')),
        ('name', HeaderItem('name', '', '', 'Common Name')),
        ('surface_x', HeaderItem('surface_x', '', '', 'Easting')),
        ('surface_y', HeaderItem('surface_y', '', '', 'Northing')),
        ('KB_elev', HeaderItem('KB_elev', '', '', 'KB elevation')),
        ('UTMzone', HeaderItem('UTMzone', '', '', 'UTM zone')),
        ('operator', HeaderItem('operator', '', '', 'operator')),
        ('status', HeaderItem('status', '', '', 'current status')),
        ('operator', HeaderItem('operator', '', '', 'operator')),
        ('status', HeaderItem('status', '', '', 'current status')),
        ('latlong', HeaderItem('status', '', (), 'latitude, longitude')),
        ('FLD', HeaderItem('FLD', '', '', 'FIELD')),
        ('LOC', HeaderItem('LOC', '', '', 'LOCATION')),
        ('PROV', HeaderItem('PROV', '', '', 'PROVINCE')),
        ('CNTY', HeaderItem('CNTY', '', '', 'COUNTY')),
        ('STAT', HeaderItem('STAT', '', '', 'STATE')),
        ('CTRY', HeaderItem('CTRY', '', '', 'COUNTRY')),
        ('SRVC', HeaderItem('SRVC', '', '', 'SERVICE COMPANY')),
    ])}


class WellError(Exception):
    """
    Generic error class.
    """
    pass


class Extra(dict):
    """
    Helper class for making dict-like things.
    """
    def __init__(self, **kwargs):
        dict.__init__(self, kwargs)
        self.__dict__ = self


class Well(las.LASReader):
    """
    Well contains everything about the well. It inherits from
    las.LASReader.

    For example, well will contain header fields, curves, and
    other data from the 'basic' LAS file.

    We will then read supplementary LAS files, and/or maybe CSV
    data, into one main other attribute of Well: the striplog.

    If we start using pandas dataframes, this is the place to
    do it.

    Args:
        f (str): The path to an LAS file.
        null_subs (float): Something to substitute for the declared
            null value, which is probably -999.25. Often it's convenient
            to use np.nan.
        unknown_as_other (bool): Whether you'd like to load unknown
            sections as plain text blocks. A hack to cope with LAS3 files
            without having to handle arbitrary sections.

    Note:
        This module is not very general. It was written to support a very
        specific workflow. If it seems to be useful for other things,
        we can come back and try to generalize it.

        Essentially, this entire thing needs to be replaced by Something
        that properly supports the LAS 3.0 format, both reading and writing.
    """
    def __init__(self, f=None,
                 lexicon=None,
                 null_subs=None,
                 unknown_as_other=True):
        # This needed ? >>>
        # OrderedDictionary.__init__(self)

        # First generate the parent object if possible.
        if f:
            super(Well, self).__init__(f, null_subs, unknown_as_other)

        self._text = ''  # what to print when printing text representation

        self.head = OrderedDictionary(DEFAULT_ITEMS['head'].items())

        # Add an empty striplog dict-like for later.
        self.striplog = Extra()

        # If we got an OTHER section, let's try loading it as striplogs...
        other = getattr(self, 'other', None)
        if other:
            f = re.MULTILINE
            pattern = re.compile(r'^(\~)(?=\w+?_Parameter)', flags=f)
            chunks = [i for i in filter(None, pattern.split(self.other))]

            # This is gross but I can't see how else to get the tilde
            # back on the strings when I do the re.split().
            nchunks = [a + b for a, b in zip(chunks[::2], chunks[1::2])]

            for section in nchunks:
                name = re.search(r'^\~(\w+?)_', section, flags=f).group(1)
                striplog = Striplog.from_las3(section, lexicon=lexicon)
                self.add_striplog(striplog, name.lower())

    # __repr__, __str__, etc, will come from LASReader

    def add_las(self, f, null_subs=None, unknown_as_other=True):
        """
        Add data from a LAS to the well object. Returns nothing.

        Args:
            f (str): The path to an LAS file.
            null_subs (float): Something to substitute for the declared
                null value, which is probably -999.25. Often it's convenient
                to use np.nan.
            unknown_as_other (bool): Whether you'd like to load unknown
                sections as plain text blocks. A hack to cope with LAS3 files
                without having to handle arbitrary sections.
        """
        pass

    def add_striplog(self, striplog, name):
        """
        Add a striplog to the well object. Returns nothing.

        Args:
            striplog (Striplog): A striplog object.
            name (str): A name for the log, e.g. 'cuttings', or 'Smith 2012'
        """
        setattr(self.striplog, name, striplog)

    def striplogs_to_las3(self, use_descriptions=False):
        """
        Form the LAS3 string.

        Notes:
            - It's debatable if this should be a ``striplog`` function, but it
                contains well-level information so I'm putting it here.
            - I can't decide whether to handle file writing, or just leave it
                to the user. So all this does for now is return a string.
        """
        data = ''
        for name, striplog in self.striplog.items():
            if name[3].lower() in 'aeiou':
                short = re.sub(r'[aeiou]', '', name)[:4].upper()
            else:
                short = name[:4].upper()
            name = name.capitalize()
            this_data = striplog.to_csv(use_descriptions=use_descriptions,
                                        header=False)
            template = templates.section
            data += template.format(name=name,
                                    short=short,
                                    source=striplog.source,
                                    data=this_data) + '\n'

        eref, apd = -999.25, -999.25
        if self.parameters.DREF.data.upper() in ['KB', "KELLY BUSHING"]:
            try:
                eref = float(self.parameters.EREF.data)
            except AttributeError:
                with warnings.catch_warnings():
                    warnings.simplefilter("always")
                    warnings.warn("There is no EREF.")

        if self.parameters.PDAT.data.upper() in ['GL', 'GROUND LEVEL']:
            try:
                apd = float(self.parameters.APD.data)
            except AttributeError:
                with warnings.catch_warnings():
                    warnings.simplefilter("always")
                    warnings.warn("There is no APD.")

        time_now = time.strftime("%Y/%m/%d %H:%M", time.gmtime())
        template = templates.las
        result = template.format(prog='striplog.py',
                                      date=time_now,
                                      start=self.start,  # NB from logs
                                      stop=self.stop,    # NB from logs
                                      step=-999.25,  # striplogs have no step
                                      null=self.null,
                                      well=self.well.WELL.data,
                                      uwi=self.well.UWI.data,
                                      lic=self.well.LIC.data,
                                      apd=apd,
                                      eref=eref,
                                      section=data,
                                      curve='')
        return result.strip() + '\n'
