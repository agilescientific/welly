"""
Defines well headers.

:copyright: 2021 Agile Scientific
:license: Apache 2.0
"""
import csv

from .fields import las_fields
from . import utils


class Header(dict):
    """
    The well metadata or header information.

    Not the same as an LAS header, but we might get info from there.
    """
    def __init__(self, params=None):
        """
        Generic initializer.
        """
        if params is None:
            params = {}
        setattr(self, 'name', '')
        setattr(self, 'uwi', '')
        for k, v in params.items():
            if k and v:
                setattr(self, k, v)
        setattr(self, 'uwi', str(self.uwi if self.uwi else ''))

    def __repr__(self):
        return self.__dict__.__repr__()

    def __setitem__(self, key, item):
        self.__dict__[key] = item
        return

    def __getitem__(self, key):
        return self.__dict__[key]

    @classmethod
    def from_lasio(cls, header, remap=None, funcs=None):
        """
        Assumes we're starting with a lasio object, l.

        Args:
            header (pd.DataFrame): Header data from las file
            remap (dict): Optional. A dict of 'old': 'new' LAS field names.
            funcs (dict): Optional. A dict of 'las field': function() for
                implementing a transform before loading. Can be a lambda.

        """
        params = {}
        for field, (sect, item) in las_fields['header'].items():
            params[field] = utils.get_header_item(header,
                                                  sect,
                                                  item,
                                                  remap=remap,
                                                  funcs=funcs)
        return cls(params)

    @classmethod
    def from_csv(cls, csv_file):
        """
        Not implemented. Will provide a route from CSV file.
        """
        try:
            param_dict = csv.DictReader(csv_file)
            return cls(param_dict)
        except:
            raise NotImplementedError
