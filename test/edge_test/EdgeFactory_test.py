"""Tests for EdgeFactory.py"""

from obspy.core import Stream, Trace, UTCDateTime
from geomagio.edge import EdgeFactory
from numpy.testing import assert_equal


def dont_get_timeseries():
    """edge_test.EdgeFactory_test.test_get_timeseries()"""
    # Call get_timeseries, and test stats for comfirmation that it came back.
    # TODO, need to pass in host and port from a config file, or manually
    #   change for a single test.
    edge_factory = EdgeFactory(host="TODO", port="TODO")
    timeseries = edge_factory.get_timeseries(
        UTCDateTime(2015, 3, 1, 0, 0, 0),
        UTCDateTime(2015, 3, 1, 1, 0, 0),
        "BOU",
        ("H"),
        "variation",
        "minute",
    )
    assert_equal(
        timeseries.select(channel="H")[0].stats.station,
        "BOU",
        "Expect timeseries to have stats",
    )
    assert_equal(
        timeseries.select(channel="H")[0].stats.channel,
        "H",
        "Expect timeseries stats channel to be equal to H",
    )
