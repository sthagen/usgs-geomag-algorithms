import numpy
from obspy import Stream, UTCDateTime
from obspy.clients.neic.client import Client

from geomagio import TimeseriesUtility
from geomagio.edge import SNCL


class MockMiniSeedClient(Client):
    """replaces default obspy miniseed client's get_waveforms method to return trace of ones

    Note: includes 'return_empty' parameter to simulate situations where no data is received
    """

    def __init__(self, return_empty: bool = False):
        self.return_empty = return_empty

    def get_waveforms(
        self,
        network: str,
        station: str,
        location: str,
        channel: str,
        starttime: UTCDateTime,
        endtime: UTCDateTime,
    ):
        if self.return_empty:
            return Stream()
        sncl = SNCL(
            station=station,
            network=network,
            channel=channel,
            location=location,
        )
        trace = TimeseriesUtility.create_empty_trace(
            starttime=starttime,
            endtime=endtime,
            observatory=station,
            channel=channel,
            type=sncl.data_type,
            interval=sncl.interval,
            network=network,
            station=station,
            location=location,
        )
        trace.data = numpy.ones(trace.stats.npts)
        return Stream([trace])


class MisalignedMiniSeedClient(MockMiniSeedClient):
    """mock client that adds an offset value to endtime"""

    def __init__(self, return_empty: bool = False, increment: int = 1):
        super().__init__(return_empty=return_empty)
        self.increment = increment
        self.offset = 0

    def get_waveforms(
        self,
        network: str,
        station: str,
        location: str,
        channel: str,
        starttime: UTCDateTime,
        endtime: UTCDateTime,
    ):
        endtime = endtime + self.offset
        self.offset = self.offset + self.increment
        return super().get_waveforms(
            network, station, location, channel, starttime, endtime
        )
