"""
==================
welly
==================
"""
from .project import Project
from .well import Well
from .header import Header
from .curve import Curve
from .synthetic import Synthetic
from .location import Location
from .crs import CRS
from . import tools
from . import quality


def read_las(path, **kwargs):
    return Project.from_las(path, **kwargs)


__all__ = [
           'Project',
           'Well',
           'Header',
           'Curve',
           'Synthetic',
           'Location',
           'CRS',
           'quality',
           'tools',  # Various classes in here
           'read_las'
          ]


__version__ = "unknown"
try:
    from ._version import __version__
except ImportError:
    pass
