import numpy
from obspy import Stream, UTCDateTime
from obspy.clients.neic.client import Client
import pytest

from geomagio import TimeseriesUtility


@pytest.fixture(scope="class")
def MockMiniSeedClient() -> Client:
    """replaces default obspy miniseed client's get_waveforms method to return trace of ones"""

    class MockMiniSeedClient(Client):
        def get_waveforms(
            self,
            network: str,
            station: str,
            location: str,
            channel: str,
            starttime: UTCDateTime,
            endtime: UTCDateTime,
        ):
            trace = TimeseriesUtility.create_empty_trace(
                starttime=starttime,
                endtime=endtime,
                observatory=station,
                channel=channel,
                type=self._get_data_type(location=location),
                interval=self._get_interval(channel=channel),
                network=network,
                station=station,
                location=location,
            )
            trace.data = numpy.ones(trace.stats.npts)
            return Stream([trace])

        def _get_interval(self, channel: str) -> str:
            channel_start = channel[0]
            if channel_start == "B":
                return "tenhertz"
            elif channel_start == "L":
                return "second"
            elif channel_start == "U":
                return "minute"
            elif channel_start == "R":
                return "hour"
            elif channel_start == "P":
                return "day"
            else:
                raise ValueError(f"Unexpected channel start: {channel_start}")

        def _get_data_type(self, location: str) -> str:
            location_start = location[0]
            if location_start == "R":
                return "variation"
            elif location_start == "A":
                return "adjusted"
            elif location_start == "Q":
                return "quasi-definitive"
            elif location_start == "D":
                return "definitive"
            else:
                raise ValueError(f"Unexpected location start: {location_start}")

    yield MockMiniSeedClient
