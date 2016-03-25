#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines a synthetic seismogram.

:copyright: 2016 Agile Geoscience
:license: Apache 2.0
"""
import numpy as np


class Synthetic(np.ndarray):
    """
    Incomplete.
    """

    def __new__(cls, data, params=None):
        obj = np.asarray(data).view(cls).copy()

        for k, v in params.items():
            setattr(obj, k, v)

        return obj

    def __array_finalize__(self, obj):
        if obj is None:
            return

        if obj.size == 1:
            return float(obj)

        self.dt = getattr(obj, 'dt', 0.001)
        self.mnemonic = getattr(obj, 'mnemonic', 'SYN')
