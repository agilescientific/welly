seisplot
========

**Manage subsurface well data.**

.. image:: https://img.shields.io/badge/status-alpha-orange.svg
    :target: #
    :alt: Project status

.. image:: https://img.shields.io/github/release/agile-geoscience/welly.svg
    :target: #
    :alt: Release

.. image:: https://img.shields.io/badge/python-3.4,_3.5-blue.svg
    :target: #
    :alt: Python version

.. image:: https://img.shields.io/badge/license-Apache_2.0-blue.svg
    :target: http://www.apache.org/licenses/LICENSE-2.0
    :alt: License


philosophy
==========

The `lasio <https://github.com/kinverarity1/lasio>`_ project provides a very nice way to read and 
write `CWLS <http://www.cwls.org/>`_ Log ASCII Standard files. The result is an object, based on
``OrderedDict``, that contains all the LAS data — it's more or less analogous to the LAS file.

Sometimes we want a higher-level object, for example to contain methods that have nothing to do 
with LAS files. We may want to handle other well data, such as deviation surveys, tops (aka picks),
engineering data, striplogs, synthetics, and so on. This is where ``welly`` comes in.

``welly`` uses ``lasio`` for data I/O, but hides much of it from the user. We recommend you look at 
both projects before deciding if you need the 'well-level' functionality that ``welly`` provides.


alpha code
==========

*This project will change continuously until April 2016.*


contributing
============

We welcome contributions! Please fork the project and submit pull requests, or get in touch with us
at `hello@agilegeoscience.com <mailto:hello@agilegeoscience.com>`_
