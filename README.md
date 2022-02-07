![Welly banner](https://www.dropbox.com/s/a8jg7zomi4wgolb/welly_banner.png?raw=1)

[![Travis build](https://img.shields.io/travis/agile-geoscience/welly.svg)](https://travis-ci.org/agile-geoscience/welly]
[![PyPI status](https://img.shields.io/pypi/status/welly.svg)](https://pypi.org/project/welly//)
[![PyPI versions](https://img.shields.io/pypi/pyversions/welly.svg)](https://pypi.org/project/welly//)
[![PyPI license](https://img.shields.io/pypi/l/welly.svg)](https://pypi.org/project/welly/)

**Welly is a family of classes to facilitate the loading, processing, and analysis of subsurface wells and well data, such as striplogs, formation tops, well log curves, and synthetic seismograms.**

Welly is a family of classes to facilitate the loading, processing, and analysis of subsurface wells and well data, such as striplogs, formation tops, well log curves, and synthetic seismograms.


## Installation

    pip install welly

For developers, there are `pip` options for installing `tests`, `docs` or `dev` (docs plus tests) dependencies.


## Quick start

```python
from welly import Well, Project

w = Well.from_las('my_wells/my_well.las')  # Load a single well.
p = Project.from_las('my_wells/*.las')     # Load lots of wells.

gr = w.data['GR']  # One log; this is a subclassed NumPy array...
gr.plot()          # ...with some superpowers!
```

Next, check out the tutorial notebooks.


## Philosophy

The [`lasio`](https://github.com/kinverarity1/lasio) project provides a very nice way to read and 
write [CWLS](http://www.cwls.org/) Log ASCII Standard files. The result is an object that contains all the LAS data — it's more or less analogous to the LAS file.

Sometimes we want a higher-level object, for example to contain methods that have nothing to do 
with LAS files. We may want to handle other well data, such as deviation surveys, tops (aka picks),
engineering data, striplogs, synthetics, and so on. This is where `welly` comes in.

`welly` uses `lasio` for data I/O, but hides much of it from the user. We recommend you look at 
both projects before deciding if you need the 'well-level' functionality that `welly` provides.


## Contributing

Please see [`CONTRIBUTING.md`](https://github.com/agile-geoscience/redflag/blob/main/CONTRIBUTING.md).


## Testing

Use `pip install .tests` to install the testing dependencies (`pytest`, `pytest-cov` and `pytest-mpl`). Then run tests with:

    python run_tests.py


## Building

This repo uses PEP 517-style packaging. [Read more about this](https://setuptools.pypa.io/en/latest/build_meta.html) and [about Python packaging in general](https://packaging.python.org/en/latest/tutorials/packaging-projects/).

Building the project requires `build`, so first:

    pip install build

Then to build `welly` locally:

    python -m build

This builds both `.tar.gz` and `.whl` files, either of which you can install with `pip`.
