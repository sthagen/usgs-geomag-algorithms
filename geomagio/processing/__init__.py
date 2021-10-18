"""Package with near-real time processing configurations.

Note that these implementations are subject to change,
and should be considered less stable than other packages in the library.
"""
from .factory import get_edge_factory, get_miniseed_factory
from .derived import adjusted, average, sqdist_minute
from .filters import minute_filter, second_filter


__all__ = [
    "adjusted",
    "average",
    "get_edge_factory",
    "get_miniseed_factory",
    "minute_filter",
    "second_filter",
    "sqdist_minute",
]
