# -*- coding: utf-8 -*-
"""
CRS functions. Modeled on fiona by Sean Gillies.
https://github.com/Toblerity/Fiona

This version...
:copyright: 2016 Agile Geoscience
:license: Apache 2.0

Original code...
Copyright (c) 2007, Sean C. Gillies
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of Sean C. Gillies nor the names of
      its contributors may be used to endorse or promote products derived from
      this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""
import collections


class CRS(collections.abc.MutableMapping):

    def __init__(self, *args, **kwargs):
        '''
        Use the object dict.
        '''
        self.__dict__.update(*args, **kwargs)

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __getitem__(self, key):
        return self.__dict__[key]

    def __delitem__(self, key):
        del self.__dict__[key]

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

    def __str__(self):
        '''returns simple dict representation of the mapping'''
        return str(self.__dict__)

    def __repr__(self):
        '''echoes class, id, & reproducible representation in the REPL'''
        return 'CRS({})'.format(self.__dict__)

    @classmethod
    def from_string(cls, prjs):
        """
        Turn a PROJ.4 string into a mapping of parameters. Bare parameters
        like "+no_defs" are given a value of ``True``. All keys are checked
        against the ``all_proj_keys`` list.

        Args:
            prjs (str): A PROJ4 string.
        """
        def parse(v):
            try:
                return int(v)
            except ValueError:
                pass
            try:
                return float(v)
            except ValueError:
                return v

        parts = [o.lstrip('+') for o in prjs.strip().split()]

        items = map(
            lambda kv: len(kv) == 2 and (kv[0], parse(kv[1])) or (kv[0], True),
            (p.split('=') for p in parts))

        return cls({k: v for k, v in items if '+'+k in PROJ4_PARAMS.keys()})

    @classmethod
    def from_epsg(cls, code):
        """
        Given an integer code, returns an EPSG-like mapping.
        Note: the input code is not validated against an EPSG database.
        """
        if int(code) <= 0:
            raise ValueError("EPSG codes are positive integers")
        return cls({'init': "epsg:{}".format(code), 'no_defs': True})

    @property
    def data(self):
        return self.__dict__

    def to_string(self):
        """
        Turn a CRS dict into a PROJ.4 string. Mapping keys are tested against
        ``all_proj_keys`` list. Values of ``True`` are omitted, leaving the key
        bare: {'no_defs': True} -> "+no_defs" and items where the value is
        otherwise not a str, int, or float are omitted.

        Args:
            crs: A CRS dict as used in Location.

        Returns:
            str. The string representation.
        """
        def filt(x):
            return '+'+x[0] in PROJ4_PARAMS.keys() and x[1] is not False

        items = []
        for k, v in sorted(filter(filt, self.items())):
            items.append(
                "+" + "=".join(
                    map(str, filter(
                        lambda y: (y or y == 0) and y is not True, (k, v)))))
        return " ".join(items)

# All of Proj4 params from...
# http://trac.osgeo.org/proj/wiki/GenParms
PROJ4_PARAMS = {'+K': '',
                '+M': '',
                '+R': '',
                '+R_A': 'Compute radius such that the area of the sphere is the same as the area of the ellipsoid',
                '+R_V': '',
                '+R_a': '',
                '+R_g': '',
                '+R_h': '',
                '+R_lat_a': '',
                '+R_lat_g': '',
                '+W': '',
                '+a': 'Semimajor radius of the ellipsoid axis',
                '+alpha': '? Used with Oblique Mercator and possibly a few others',
                '+axis': 'Axis orientation (new in 4.8.0)',
                '+azi': '',
                '+b': 'Semiminor radius of the ellipsoid axis',
                '+belgium': '',
                '+beta': '',
                '+czech': '',
                '+datum': 'Datum name (see `proj -ld`)',
                '+e': 'Eccentricity of the ellipsoid = sqrt(1 - b^2/a^2) = sqrt( f*(2-f) )',
                '+ellps': 'Ellipsoid name (see `proj -le`)',
                '+es': 'Eccentricity of the ellipsoid squared',
                '+f': 'Flattening of the ellipsoid (often presented as an inverse, e.g. 1/298)',
                '+gamma': '',
                '+geoc': '',
                '+guam': '',
                '+h': '',
                '+init': 'Initialize from a named CRS',
                '+k': 'Scaling factor (old name)',
                '+k_0': 'Scaling factor (new name)',
                '+lat_0': 'Latitude of origin',
                '+lat_1': 'Latitude of first standard parallel',
                '+lat_2': 'Latitude of second standard parallel',
                '+lat_b': '',
                '+lat_t': '',
                '+lat_ts': 'Latitude of true scale',
                '+lon_0': 'Central meridian',
                '+lon_1': '',
                '+lon_2': '',
                '+lon_wrap': 'Center longitude to use for wrapping (see below)',
                '+lonc': '? Longitude used with Oblique Mercator and possibly a few others',
                '+lsat': '',
                '+m': '',
                '+n': '',
                '+nadgrids': 'Filename of NTv2 grid file to use for datum transforms (see below)',
                '+no_cut': '',
                '+no_defs': "Don't use the /usr/share/proj/proj_def.dat defaults file",
                '+no_off': '',
                '+no_rot': '',
                '+ns': '',
                '+o_alpha': '',
                '+o_lat_1': '',
                '+o_lat_2': '',
                '+o_lat_c': '',
                '+o_lat_p': '',
                '+o_lon_1': '',
                '+o_lon_2': '',
                '+o_lon_c': '',
                '+o_lon_p': '',
                '+o_proj': '',
                '+over': '',
                '+p': '',
                '+path': '',
                '+pm': 'Alternate prime meridian (typically a city name, see below)',
                '+proj': 'Projection name (see `proj -l`)',
                '+q': '',
                '+rf': 'Reciprocal of the ellipsoid flattening term (e.g. 298)',
                '+rot': '',
                '+s': '',
                '+south': 'Denotes southern hemisphere UTM zone',
                '+sym': '',
                '+t': '',
                '+theta': '',
                '+tilt': '',
                '+to_meter': 'Multiplier to convert map units to 1.0m',
                '+towgs84': '3 or 7 term datum transform parameters (see below)',
                '+units': 'meters, US survey feet, etc.',
                '+vopt': '',
                '+vto_meter': 'vertical conversion to meters.',
                '+vunits': 'vertical units.',
                '+westo': '',
                '+x_0': 'False easting',
                '+y_0': 'False northing',
                '+zone': 'UTM zone'
                }
