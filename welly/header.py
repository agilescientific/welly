cd #!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines well headers.

:copyright: 2015 Agile Geoscience
:license: Apache 2.0
"""
from .well import WellError

import csv


class Header (object):
    def __init__(self, properties):
        for k, v in properties.items():
            if k and v:
                setattr(self, k, v)

    def __repr__(self):
    	return self.__dict__.repr()

    @classmethod
    def from_csv(cls, csv_file):
        #<munch CSV>

        param_dict = csv.DictReader()
    	return cls(param_dict)


