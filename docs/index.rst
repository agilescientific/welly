:hide-toc:

.. container:: noclass
   :name: forkongithub

   `Fork on GitHub <https://github.com/agile-geoscience/welly>`_


Welly: Splash About in Well Data
================================

    | ``welly`` facilitates the loading, processing, and analysis of subsurface wells and well data, such as striplogs, formation tops, well log curves, and synthetic seismograms.

Welly runs on Python 3.6+ with no other dependencies. It is licensed under a business-friendly Apache 2.0 license.

Getting started
---------------

To install ``welly``, simply::

    pip install welly

To load some wells from LAS files::

    import welly
    project = welly.read_las("path/to/well_*.las")

The project is a collection of well objects, each of which contains well logs. Plot the gamma-ray like::

    gr = project[0].data['GR']
    gr.plot()

Carry on exploring with the user guide below.


User guide
----------

.. toctree::
    :maxdepth: 2
    :caption: User guide

    installation
    _notebooks/Quick_start.ipynb
    _notebooks/Wells.ipynb


API reference
-------------

.. toctree::
    :maxdepth: 2
    :caption: API reference

    welly


Other resources
---------------

.. toctree::
    :maxdepth: 2
    :caption: Other resources

    development
    contributing
    authors
    license
    changelog


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. toctree::
    :caption: Project links
    :hidden:

    PyPI releases <https://pypi.org/project/welly/>
    Code in GitHub <https://github.com/agile-geoscience/welly>
    Issue tracker <https://github.com/agile-geoscience/welly/issues>
    Community guidelines <https://code.agilescientific.com/community>
    Agile's software <https://code.agilescientific.com>
    Agile's website <https://www.agilescientific.com>
