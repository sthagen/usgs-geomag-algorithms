"""Tests for EdgeFactory.py"""

from obspy.core import Stream, Trace, UTCDateTime
from geomagio.edge import EdgeFactory
from numpy.testing import assert_equal


def test_get_timeseries():
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
    assert_equal(
        timeseries.select(channel="H")[0].stats.data_type,
        "variation",
        "Expect timeseries stats data_type to be equal to variation",
    )
    # timeseries requested with location code as type
    timeseries = edge_factory.get_timeseries(
        UTCDateTime(2015, 3, 1, 0, 0, 0),
        UTCDateTime(2015, 3, 1, 1, 0, 0),
        "BOU",
        ("H"),
        "R0",
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
    assert_equal(
        timeseries.select(channel="H")[0].stats.data_type,
        "variation",
        "Expect timeseries stats data_type to be equal to variation",
    )


def test_add_empty_channels():
    """edge_test.EdgeFactory_test.test_add_empty_channels()"""
    edge_factory = EdgeFactory(host="TODO", port="TODO")
    timeseries = edge_factory.get_timeseries(
        UTCDateTime(2015, 3, 1, 0, 0, 0),
        UTCDateTime(2015, 3, 1, 1, 0, 0),
        "BOU",
        ("H"),
        "variation",
        "minute",
        add_empty_channels=False,
    )
    assert len(timeseries) == 0
    timeseries = edge_factory.get_timeseries(
        UTCDateTime(2015, 3, 1, 0, 0, 0),
        UTCDateTime(2015, 3, 1, 1, 0, 0),
        "BOU",
        ("H"),
        "variation",
        "minute",
        add_empty_channels=True,  # default
    )
    assert len(timeseries) == 1
