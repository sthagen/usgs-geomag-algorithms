"""Tests for MiniSeedFactory.py"""
import io

import numpy
from numpy.testing import assert_equal
from obspy.core import read, Stats, Stream, Trace, UTCDateTime

from geomagio import TimeseriesUtility
from geomagio.edge import MiniSeedFactory, MiniSeedInputClient


class MockMiniSeedInputClient(object):
    def __init__(self):
        self.close_called = False
        self.last_sent = None

    def close(self):
        self.close_called = True

    def send(self, stream):
        self.last_sent = stream


def test__put_timeseries():
    """edge_test.MiniSeedFactory_test.test__put_timeseries()"""
    trace1 = __create_trace([0, 1, 2, 3, numpy.nan, 5, 6, 7, 8, 9], channel="H")
    client = MockMiniSeedInputClient()
    factory = MiniSeedFactory()
    factory.write_client = client
    factory.put_timeseries(Stream(trace1), channels=("H"))
    # put timeseries should call close when done
    assert_equal(client.close_called, True)
    # trace should be split in 2 blocks at gap
    sent = client.last_sent
    assert_equal(len(sent), 2)
    # first trace includes [0...4]
    assert_equal(sent[0].stats.channel, "LFH")
    assert_equal(len(sent[0]), 4)
    assert_equal(sent[0].stats.endtime, trace1.stats.starttime + 3)
    # second trace includes [5...9]
    assert_equal(sent[1].stats.channel, "LFH")
    assert_equal(len(sent[1]), 5)
    assert_equal(sent[1].stats.starttime, trace1.stats.starttime + 5)
    assert_equal(sent[1].stats.endtime, trace1.stats.endtime)


def test__pre_process():
    """edge_test.MiniSeedFactory_test.test__pre_process()"""
    trace = __create_trace(numpy.arange((86400 * 2) + 1), channel="H")
    processed = MiniSeedInputClient(host=None)._pre_process(stream=Stream(trace))
    assert len(processed) == 2
    for trace in processed:
        assert trace.data.dtype == "float32"
        stats = trace.stats
        assert stats.npts == 86400
        assert stats.starttime.timestamp % 86400 == 0
        assert stats.endtime.timestamp % 86400 != 0


def test__format_miniseed():
    """edge_test.MiniseedFactory_test.test__format_miniseed()"""
    buf = io.BytesIO()
    trace = __create_trace(numpy.arange((86400 * 2) + 1), channel="H")
    MiniSeedInputClient(host=None)._format_miniseed(stream=Stream(trace), buf=buf)
    block_size = 512
    data = buf.getvalue()
    n_blocks = int(len(data) / block_size)
    assert n_blocks == 1516
    # 759th block is start of second day(758 blocks per day for 1Hz data)
    block_start = 758 * block_size
    block = data[block_start : block_start + block_size]
    out_stream = read(io.BytesIO(block))
    assert out_stream[0].stats.starttime.timestamp % 86400 == 0


def test__set_metadata():
    """edge_test.MiniSeedFactory_test.test__set_metadata()"""
    # Call _set_metadata with 2 traces,  and make certain the stats get
    # set for both traces.
    trace1 = Trace()
    trace2 = Trace()
    stream = Stream(traces=[trace1, trace2])
    MiniSeedFactory()._set_metadata(stream, "BOU", "H", "variation", "minute")
    assert_equal(stream[0].stats["channel"], "H")
    assert_equal(stream[1].stats["channel"], "H")


# def test_get_timeseries():
def dont_get_timeseries():
    """edge_test.MiniSeedFactory_test.test_get_timeseries()"""
    # Call get_timeseries, and test stats for comfirmation that it came back.
    # TODO, need to pass in host and port from a config file, or manually
    #   change for a single test.
    edge_factory = MiniSeedFactory(host="TODO", port="TODO")
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


def __create_trace(
    data,
    network="NT",
    station="BOU",
    channel="H",
    location="R0",
    data_interval="second",
    data_type="variation",
):
    """
    Utility to create a trace containing the given numpy array.

    Parameters
    ----------
    data: array
        The array to be inserted into the trace.

    Returns
    -------
    obspy.core.Stream
        Stream containing the channel.
    """
    stats = Stats()
    stats.starttime = UTCDateTime("2019-12-01")
    stats.delta = TimeseriesUtility.get_delta_from_interval(data_interval)
    stats.channel = channel
    stats.station = station
    stats.npts = len(data)
    stats.data_interval = data_interval
    stats.data_type = data_type
    numpy_data = numpy.array(data, dtype=numpy.float64)
    return Trace(numpy_data, stats)
