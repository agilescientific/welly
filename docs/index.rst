.. welly documentation master file, created by
   sphinx-quickstart on Mon Mar 28 15:23:23 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to welly's documentation!
=================================

Welly is a family of classes to facilitate the loading, processing, and analysis of subsurface wells and well data, such as striplogs, well log curves, and synthetic seismograms. 


Requirements
------------

* `NumPy`, which handles the numerics.
* `matplotlib`, a plotting library.
* `SciPy`, which handles curve interpolation.
* `lasio`, for reading and writing LAS files.
* `striplog`, highly recommended for helping control plotting.


The code
--------

.. toctree::
   :maxdepth: 2
   :caption: Contents:

.. automodule:: welly

.. autoclass:: Well
    :members:

.. autoclass:: Project
    :members:

.. autoclass:: Curve
    :members:

.. autoclass:: Header
    :members:

.. autoclass:: Location
    :members:

.. autoclass:: CRS
    :members:

.. autoclass:: Synthetic
    :members:


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

