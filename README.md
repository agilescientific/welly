![Welly banner](https://www.dropbox.com/s/a8jg7zomi4wgolb/welly_banner.png?raw=1)

[![Run tests](https://github.com/agile-geoscience/welly/actions/workflows/run-tests.yml/badge.svg)](https://github.com/agile-geoscience/welly/actions/workflows/run-tests.yml)
[![Build docs](https://github.com/agile-geoscience/welly/actions/workflows/build-docs.yml/badge.svg)](https://github.com/agile-geoscience/welly/actions/workflows/build-docs.yml)
[![PyPI version](https://img.shields.io/pypi/v/welly.svg)](https://pypi.python.org/pypi/welly/)
[![PyPI versions](https://img.shields.io/pypi/pyversions/welly.svg)](https://pypi.org/project/welly//)
[![PyPI license](https://img.shields.io/pypi/l/welly.svg)](https://pypi.org/project/welly/)

**`welly` facilitates the loading, processing, and analysis of subsurface wells and well data, such as striplogs, formation tops, well log curves, and synthetic seismograms.**


## Installation

    pip install welly

For developers, there are `pip` options for installing `test`, `docs` or `dev` (docs plus test) dependencies.


## Quick start

```python
from welly import Well, Project

w = Well.from_las('my_wells/my_well.las')  # Load a single well.
p = Project.from_las('my_wells/*.las')     # Load lots of wells.

gr = w.data['GR']  # One log...
gr.plot()          # ...with some superpowers!
```

Next, check out the tutorial notebooks.


## Documentation

[The `welly` documentation](https://code.agilescientific.com/welly) is a work in progress.


## Contributing

Please see [`CONTRIBUTING.md`](https://github.com/agile-geoscience/redflag/blob/main/CONTRIBUTING.md).


## Philosophy

The [`lasio`](https://github.com/kinverarity1/lasio) project provides a very nice way to read and 
write [CWLS](http://www.cwls.org/) Log ASCII Standard files. The result is an object that contains all the LAS data — it's more or less analogous to the LAS file.

Sometimes we want a higher-level object, for example to contain methods that have nothing to do 
with LAS files. We may want to handle other well data, such as deviation surveys, tops (aka picks),
engineering data, striplogs, synthetics, and so on. This is where `welly` comes in.

`welly` uses `lasio` for data I/O, but hides much of it from the user. We recommend you look at 
both projects before deciding if you need the 'well-level' functionality that `welly` provides.
