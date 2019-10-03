welly
========

**Manage subsurface well data.**

.. image:: https://img.shields.io/travis/agile-geoscience/welly.svg
    :target: https://travis-ci.org/agile-geoscience/welly
    :alt: Travis build status
    
.. image:: https://img.shields.io/pypi/status/welly.svg
    :target: https://pypi.python.org/pypi/welly/
    :alt: Development status

.. image:: https://img.shields.io/pypi/v/welly.svg
    :target: https://pypi.python.org/pypi/welly/
    :alt: Latest version
    
.. image:: https://img.shields.io/pypi/pyversions/welly.svg
    :target: https://pypi.python.org/pypi/welly/
    :alt: Python version

.. image:: https://img.shields.io/pypi/l/welly.svg
    :target: http://www.apache.org/licenses/LICENSE-2.0
    :alt: License

Welly is a family of classes to facilitate the loading, processing, and analysis of subsurface wells and well data, such as striplogs, formation tops, well log curves, and synthetic seismograms.


Philosophy
==========

The `lasio <https://github.com/kinverarity1/lasio>`_ project provides a very nice way to read and 
write `CWLS <http://www.cwls.org/>`_ Log ASCII Standard files. The result is an object, based on
``OrderedDict``, that contains all the LAS data — it's more or less analogous to the LAS file.

Sometimes we want a higher-level object, for example to contain methods that have nothing to do 
with LAS files. We may want to handle other well data, such as deviation surveys, tops (aka picks),
engineering data, striplogs, synthetics, and so on. This is where ``welly`` comes in.

``welly`` uses ``lasio`` for data I/O, but hides much of it from the user. We recommend you look at 
both projects before deciding if you need the 'well-level' functionality that ``welly`` provides.

Links
==========
`Documentation <https://welly.readthedocs.io/en/latest/>`_ 

Contributing
============

We welcome contributions! Please fork the project and submit pull requests, or get in touch with us
at `hello@agilegeoscience.com <mailto:hello@agilegeoscience.com>`_
